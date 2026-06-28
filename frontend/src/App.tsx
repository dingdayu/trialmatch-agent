import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react"
import {
  clearSession,
  createCriterion,
  createProject,
  createSubject,
  exportReport,
  fetchAuditLogs,
  fetchCriteria,
  fetchEvaluationDetail,
  fetchFile,
  fetchFiles,
  fetchHealth,
  fetchLatestEvaluations,
  fetchMe,
  fetchProjects,
  fetchProject,
  fetchSubject,
  fetchSubjects,
  generateCriteriaFromProtocol,
  getStoredToken,
  getStoredUser,
  login,
  executeScreening,
  startScreening,
  submitManualReview,
  updateCriterion,
  uploadProjectFile,
  uploadSubjectFile,
  updateProject,
} from "./api"
import { badgeClass, projectStatusLabel, resultLabel } from "./status"
import type { AuditLog, Criterion, Evaluation, EvaluationDetail, Project, Subject, UploadedFile, User } from "./types"
import { CardTitle, DataCard, EmptyState, ErrorBanner, MetricCard, PageHeader } from "./ui"

type View = "login" | "projects" | "project" | "subject" | "audit"

type Route = {
  view: View
  projectId?: string
  subjectId?: string
}

type AppData = {
  projects: Project[]
  subjects: Subject[]
  criteria: Criterion[]
  files: UploadedFile[]
  evaluations: Evaluation[]
  selectedEvaluation: EvaluationDetail | null
  auditLogs: AuditLog[]
}

const initialData: AppData = {
  projects: [],
  subjects: [],
  criteria: [],
  files: [],
  evaluations: [],
  selectedEvaluation: null,
  auditLogs: [],
}

function parseRoute(): Route {
  const hash = window.location.hash.replace(/^#\/?/, "")
  const parts = hash.split("/").filter(Boolean)

  if (parts[0] === "login") {
    return { view: "login" }
  }
  if (parts[0] === "audit") {
    return { view: "audit" }
  }
  if (parts[0] === "projects" && parts[1] !== undefined) {
    return { view: "project", projectId: parts[1] }
  }
  if (parts[0] === "subjects" && parts[1] !== undefined) {
    return { view: "subject", subjectId: parts[1] }
  }
  return { view: getStoredToken() === null ? "login" : "projects" }
}

function navigate(path: string): void {
  window.location.hash = path
}

const PARSE_POLL_INTERVAL_MS = 2000
const PARSE_POLL_MAX_ATTEMPTS = 60

async function pollParseStatus(fileId: string): Promise<string> {
  for (let attempt = 0; attempt < PARSE_POLL_MAX_ATTEMPTS; attempt += 1) {
    const file = await fetchFile(fileId)
    if (file.parse_status === "completed" || file.parse_status === "failed") {
      return file.parse_status
    }
    await new Promise((resolve) => setTimeout(resolve, PARSE_POLL_INTERVAL_MS))
  }
  return "timeout"
}

export function App() {
  const [route, setRoute] = useState<Route>(() => parseRoute())
  const [user, setUser] = useState<User | null>(() => getStoredUser())
  const [data, setData] = useState<AppData>(initialData)
  const [project, setProject] = useState<Project | null>(null)
  const [subject, setSubject] = useState<Subject | null>(null)
  const [health, setHealth] = useState<{ status: string; database?: string; version?: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    const onHashChange = () => setRoute(parseRoute())
    window.addEventListener("hashchange", onHashChange)
    return () => window.removeEventListener("hashchange", onHashChange)
  }, [])

  useEffect(() => {
    void fetchHealth()
      .then(setHealth)
      .catch((err: unknown) => setHealth({ status: err instanceof Error ? err.message : "unreachable" }))
  }, [])

  const loadProjects = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [me, projectsPage] = await Promise.all([fetchMe(), fetchProjects()])
      setUser(me)
      setData((current) => ({ ...current, projects: projectsPage.items }))
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载项目失败")
      if (getStoredToken() === null) {
        navigate("/login")
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const loadProjectWorkspace = useCallback(async (projectId: string) => {
    setLoading(true)
    setError(null)
    setData((current) => ({ ...current, files: [], evaluations: [], selectedEvaluation: null }))
    try {
      const [projectData, subjectsPage, criteriaData, filesPage] = await Promise.all([
        fetchProject(projectId),
        fetchSubjects(projectId),
        fetchCriteria(projectId),
        fetchFiles(projectId, undefined, "project_protocol"),
      ])
      setProject(projectData)
      setData((current) => ({
        ...current,
        subjects: subjectsPage.items,
        criteria: criteriaData,
        files: filesPage.items,
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载项目详情失败")
    } finally {
      setLoading(false)
    }
  }, [])

  const loadSubjectWorkspace = useCallback(async (subjectId: string, silent = false) => {
    if (!silent) {
      setLoading(true)
      setError(null)
      setData((current) => ({ ...current, files: [], evaluations: [], selectedEvaluation: null }))
    }
    try {
      const latest = await fetchLatestEvaluations(subjectId)
      const subjectData = latest.subject ?? await fetchSubject(subjectId)
      const projectData = latest.project ?? await fetchProject(subjectData.project_id)
      let filesPage: UploadedFile[] = []
      let selectedEvaluation: EvaluationDetail | null = null

      const files = await fetchFiles(projectData.id, subjectData.id, "subject_data")
      filesPage = files.items
      const firstReview = latest.evaluations.find(
        (item) => item.ai_result === "manual_review" || item.ai_result === "insufficient_data",
      ) ?? latest.evaluations[0]
      if (firstReview !== undefined) {
        selectedEvaluation = await fetchEvaluationDetail(firstReview.id)
      }

      setSubject(subjectData)
      setProject(projectData)
      setData((current) => ({
        ...current,
        files: filesPage,
        evaluations: latest.evaluations,
        selectedEvaluation: silent ? (current.selectedEvaluation ?? selectedEvaluation) : selectedEvaluation,
      }))
    } catch (err) {
      if (!silent) {
        setError(err instanceof Error ? err.message : "加载初筛结果失败")
      }
    } finally {
      if (!silent) {
        setLoading(false)
      }
    }
  }, [])

  const loadAudit = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const logs = await fetchAuditLogs()
      setData((current) => ({ ...current, auditLogs: logs.items }))
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载审计日志失败")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (route.view === "projects") {
      void loadProjects()
    }
    if (route.view === "project" && route.projectId !== undefined) {
      void loadProjectWorkspace(route.projectId)
    }
    if (route.view === "subject" && route.subjectId !== undefined) {
      void loadSubjectWorkspace(route.subjectId)
    }
    if (route.view === "audit") {
      void loadAudit()
    }
  }, [loadAudit, loadProjectWorkspace, loadProjects, loadSubjectWorkspace, route])

  useEffect(() => {
    if (route.view !== "subject" || route.subjectId === undefined) {
      return
    }
    const inProgress = subject?.screening_status === "screening" || subject?.screening_status === "parsing" || subject?.screening_status === "matching"
    if (!inProgress) {
      return
    }
    const timer = window.setInterval(() => {
      void loadSubjectWorkspace(route.subjectId ?? "", true)
    }, 4000)
    return () => window.clearInterval(timer)
  }, [route.view, route.subjectId, subject?.screening_status, loadSubjectWorkspace])

  const handleLogout = () => {
    clearSession()
    setUser(null)
    setData(initialData)
    navigate("/login")
  }

  if (route.view === "login") {
    return (
      <LoginPage
        health={health}
        onLogin={async (username, password) => {
          setError(null)
          const response = await login(username, password)
          setUser(response.user)
          navigate("/projects")
        }}
        error={error}
        setError={setError}
      />
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="sidebar-brand naked-button" type="button" onClick={() => navigate("/projects")}>
          <span className="brand-mark">TM</span>
          <span>
            <strong>TrialMatch Agent</strong>
            <small>研筛通</small>
          </span>
        </button>
        <nav className="sidebar-nav" aria-label="主导航">
          <button className="sidebar-link" type="button" onClick={() => navigate("/projects")}>
            <span>P</span>项目工作台
          </button>
          <button className="sidebar-link" type="button" onClick={() => navigate("/audit")}>
            <span>A</span>审计日志
          </button>
        </nav>
        <div className="sidebar-card">
          <span className="tag tag-info">Python Backend</span>
          <p>已对接 `/api/v1`，AI 初筛建议必须绑定证据，并由 CRC 或研究者人工确认后使用。</p>
        </div>
      </aside>
      <div className="workspace">
        <header className="workspace-topbar">
          <div>
            <strong>临床证据工作台</strong>
            <p>criterion → judgment → citation → document chunk</p>
          </div>
          <div className="topbar-actions">
            <span className={health?.status === "ok" ? "tag tag-success" : "tag tag-warning"}>
              API {health?.status ?? "checking"}
            </span>
            <button className="btn btn-ghost" type="button" onClick={handleLogout}>
              {user?.display_name ?? user?.username ?? "退出"}
            </button>
          </div>
        </header>
        <main className="content-frame">
          <ErrorBanner message={error} />
          {notice === null ? null : <div className="notice-banner">{notice}</div>}
          {loading ? <div className="loading-bar">正在从后端同步数据…</div> : null}
          {parsing ? <div className="loading-bar">正在解析处理上传的文件，请稍候…</div> : null}
          {route.view === "projects" ? (
            <ProjectsPage
              projects={data.projects}
              onCreate={async (form) => {
                await createProject(form)
                setNotice("项目已创建")
                await loadProjects()
              }}
            />
          ) : null}
          {route.view === "project" && route.projectId !== undefined ? (
            <ProjectWorkspace
              project={project}
              subjects={data.subjects}
              criteria={data.criteria}
              files={data.files}
              onCreateSubject={async (form) => {
                setError(null)
                try {
                  await createSubject(route.projectId ?? "", form)
                  setNotice("受试者已创建")
                  await loadProjectWorkspace(route.projectId ?? "")
                } catch (err) {
                  setError(err instanceof Error ? err.message : "新增受试者失败")
                  throw err
                }
              }}
              onCreateCriterion={async (form) => {
                await createCriterion(route.projectId ?? "", form)
                setNotice("入排标准已新增")
                await loadProjectWorkspace(route.projectId ?? "")
              }}
              onUpdatePrompt={async (aiPrompt) => {
                await updateProject(route.projectId ?? "", { ai_prompt: aiPrompt })
                setNotice("项目级 AI 提示词已保存")
                await loadProjectWorkspace(route.projectId ?? "")
              }}
              onUploadProjectFile={async (file, fileType) => {
                const projectId = route.projectId ?? ""
                const uploaded = await uploadProjectFile(projectId, file, fileType)
                setNotice("文件已上传，正在解析中…")
                setParsing(true)
                try {
                  const status = await pollParseStatus(uploaded.id)
                  if (status === "completed") {
                    setNotice("文件解析完成")
                  } else if (status === "failed") {
                    setError("文件解析失败，请重试")
                  } else {
                    setNotice("解析耗时较长，请稍后刷新查看")
                  }
                } finally {
                  setParsing(false)
                }
                await loadProjectWorkspace(projectId)
              }}
              onGenerateCriteria={async () => {
                const projectId = route.projectId ?? ""
                setError(null)
                try {
                  const result = await generateCriteriaFromProtocol(projectId)
                  if (result.generated_count === 0) {
                    setNotice("未能从方案中识别入排标准，请检查方案文件")
                  } else {
                    setNotice(`AI 已生成 ${result.generated_count} 条入排标准草稿，请确认`)
                  }
                  await loadProjectWorkspace(projectId)
                } catch (err) {
                  setError(err instanceof Error ? err.message : "AI 生成入排标准失败")
                }
              }}
              onConfirmCriterion={async (criterionId) => {
                setError(null)
                try {
                  await updateCriterion(criterionId, { review_status: "confirmed", is_active: true })
                  setNotice("已确认采用该入排标准")
                  await loadProjectWorkspace(route.projectId ?? "")
                } catch (err) {
                  setError(err instanceof Error ? err.message : "确认入排标准失败")
                  throw err
                }
              }}
              onConfirmAllCriteria={async (criterionIds) => {
                setError(null)
                try {
                  await Promise.all(
                    criterionIds.map((id) =>
                      updateCriterion(id, { review_status: "confirmed", is_active: true }),
                    ),
                  )
                  setNotice(`已全部采用 ${criterionIds.length} 条入排标准`)
                  await loadProjectWorkspace(route.projectId ?? "")
                } catch (err) {
                  setError(err instanceof Error ? err.message : "全部采用失败")
                  throw err
                }
              }}
            />
          ) : null}
          {route.view === "subject" && route.subjectId !== undefined ? (
            <SubjectScreeningPage
              project={project}
              subject={subject}
              files={data.files}
              evaluations={data.evaluations}
              selectedEvaluation={data.selectedEvaluation}
              onSelectEvaluation={async (evaluationId) => {
                const detail = await fetchEvaluationDetail(evaluationId)
                setData((current) => ({ ...current, selectedEvaluation: detail }))
              }}
              onStartScreening={async () => {
                const subjectId = route.subjectId ?? ""
                setError(null)
                setNotice("AI 初筛进行中，正在逐条匹配入排标准…")
                setParsing(true)
                try {
                  const run = await startScreening(subjectId)
                  const result = await executeScreening(subjectId, run.id)
                  setNotice(
                    `AI 初筛完成：共评估 ${result.evaluation_count ?? 0} 条标准`,
                  )
                  await loadSubjectWorkspace(subjectId)
                } catch (err) {
                  setError(err instanceof Error ? err.message : "启动 AI 初筛失败")
                } finally {
                  setParsing(false)
                }
              }}
              onExport={async () => {
                const task = await exportReport(route.subjectId ?? "")
                setNotice(`报告已生成：${task.download_url ?? task.export_task_id}`)
              }}
              onManualReview={async (evaluationId, manualResult, manualComment, reviewStatus) => {
                await submitManualReview(evaluationId, {
                  manual_result: manualResult,
                  manual_comment: manualComment,
                  review_status: reviewStatus,
                })
                setNotice("人工复核结果已保存")
                await loadSubjectWorkspace(route.subjectId ?? "")
              }}
              onUploadSubjectFile={async (file, fileType) => {
                const subjectId = route.subjectId ?? ""
                const uploaded = await uploadSubjectFile(subjectId, file, fileType)
                setNotice("资料已上传，正在多模态解析并触发入排匹配…")
                setParsing(true)
                try {
                  const status = await pollParseStatus(uploaded.id)
                  if (status === "completed") {
                    setNotice("解析完成，AI 入排匹配结果已更新")
                  } else if (status === "failed") {
                    setError("文件解析失败，请重试")
                  } else {
                    setNotice("解析耗时较长，请稍后刷新查看")
                  }
                } finally {
                  setParsing(false)
                }
                await loadSubjectWorkspace(subjectId)
              }}
            />
          ) : null}
          {route.view === "audit" ? <AuditPage logs={data.auditLogs} /> : null}
        </main>
      </div>
    </div>
  )
}

function LoginPage({
  health,
  onLogin,
  error,
  setError,
}: {
  readonly health: { status: string; database?: string; version?: string } | null
  readonly onLogin: (username: string, password: string) => Promise<void>
  readonly error: string | null
  readonly setError: (message: string | null) => void
}) {
  const [busy, setBusy] = useState(false)

  return (
    <div className="login-shell">
      <section className="login-hero">
        <div>
          <span className="tag tag-success">Clinical Evidence Matching</span>
          <h1>研筛通，让每一次 AI 初筛都有证据链。</h1>
          <p className="muted">CRC 上传材料后，系统解析文件、匹配入排标准，并把判断、理由、引用和原始 chunk 串成可复核链路。</p>
        </div>
        <div className="grid-3">
          <MetricCard label="后端状态" tone={health?.status === "ok" ? "success" : "warning"} value={health?.status ?? "检查中"} />
          <MetricCard label="数据库" tone="info" value={health?.database ?? "unknown"} />
          <MetricCard label="默认账号" tone="warning" value="admin" />
        </div>
      </section>
      <section className="login-panel">
        <form
          className="login-card field"
          onSubmit={(event) => {
            event.preventDefault()
            const form = new FormData(event.currentTarget)
            const username = String(form.get("username") ?? "")
            const password = String(form.get("password") ?? "")
            setBusy(true)
            setError(null)
            void onLogin(username, password)
              .catch((err: unknown) => setError(err instanceof Error ? err.message : "登录失败"))
              .finally(() => setBusy(false))
          }}
        >
          <span className="eyebrow">Secure Login</span>
          <h2>登录工作台</h2>
          <p className="muted">使用后端默认账号 admin/admin123、crc001/123456 或 pm001/123456 进入系统。</p>
          <ErrorBanner message={error} />
          <label className="field">
            <span>用户名</span>
            <input className="input" name="username" defaultValue="admin" required />
          </label>
          <label className="field">
            <span>密码</span>
            <input className="input" name="password" defaultValue="admin123" required type="password" />
          </label>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "登录中…" : "进入项目工作台"}
          </button>
        </form>
      </section>
    </div>
  )
}

function ProjectsPage({
  projects,
  onCreate,
}: {
  readonly projects: Project[]
  readonly onCreate: (form: { project_no: string; study_name: string; indication?: string; phase?: string; sponsor?: string }) => Promise<void>
}) {
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const activeProjects = projects.filter((item) => item.status === "screening" || item.status === "active").length

  return (
    <>
      <PageHeader
        kicker="Projects"
        title="项目工作台"
        description="集中查看筛选中、配置中和暂停的临床研究项目，并进入项目配置、受试者管理和证据链复核。"
        actions={<button className="btn btn-primary" type="button" onClick={() => setIsCreateOpen(true)}>新增项目</button>}
      />
      <section className="grid-4">
        <MetricCard label="项目总数" value={projects.length} />
        <MetricCard label="启用/筛选中" tone="success" value={activeProjects} />
        <MetricCard label="接口来源" tone="info" value="FastAPI" />
        <MetricCard label="认证方式" tone="warning" value="JWT" />
      </section>
      <DataCard>
        <CardTitle title="研究项目" meta={`${projects.length} 个项目`} />
        {projects.length === 0 ? (
          <EmptyState>暂无项目。请先创建一个临床研究项目。</EmptyState>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>项目编号</th>
                  <th>研究名称</th>
                  <th>适应症/阶段</th>
                  <th>申办方</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((item) => (
                  <tr key={item.id}>
                    <td className="mono">{item.project_no}</td>
                    <td>
                      <strong>{item.study_name}</strong>
                      <p className="caption">{item.study_short_name ?? "—"}</p>
                    </td>
                    <td>{item.indication ?? "未配置"} · {item.phase ?? "未配置"}</td>
                    <td>{item.sponsor ?? "—"}</td>
                    <td><span className={badgeClass(item.status)}>{projectStatusLabel(item.status)}</span></td>
                    <td>
                      <button className="btn btn-primary" type="button" onClick={() => navigate(`/projects/${item.id}`)}>
                        进入项目
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </DataCard>
      <Modal isOpen={isCreateOpen} title="新建项目" onClose={() => setIsCreateOpen(false)}>
        <ProjectForm
          onSubmit={async (form) => {
            await onCreate(form)
            setIsCreateOpen(false)
          }}
        />
      </Modal>
    </>
  )
}

function Modal({
  isOpen,
  title,
  children,
  onClose,
}: {
  readonly isOpen: boolean
  readonly title: string
  readonly children: ReactNode
  readonly onClose: () => void
}) {
  if (!isOpen) {
    return null
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        aria-modal="true"
        className="modal-card"
        role="dialog"
        aria-labelledby="modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <span className="eyebrow">Form</span>
            <h2 id="modal-title">{title}</h2>
          </div>
          <button className="btn btn-ghost" type="button" onClick={onClose}>关闭</button>
        </div>
        {children}
      </section>
    </div>
  )
}

function ProjectForm({
  onSubmit,
}: {
  readonly onSubmit: (form: { project_no: string; study_name: string; indication?: string; phase?: string; sponsor?: string }) => Promise<void>
}) {
  return (
    <form
      className="form-grid card-pad"
      onSubmit={(event) => {
        event.preventDefault()
        const form = new FormData(event.currentTarget)
        void onSubmit({
          project_no: String(form.get("project_no") ?? ""),
          study_name: String(form.get("study_name") ?? ""),
          indication: String(form.get("indication") ?? ""),
          phase: String(form.get("phase") ?? ""),
          sponsor: String(form.get("sponsor") ?? ""),
        }).then(() => event.currentTarget.reset())
      }}
    >
      <label className="field"><span>项目编号</span><input className="input" name="project_no" placeholder="KM-CRC-2026-001" required /></label>
      <label className="field"><span>研究名称</span><input className="input" name="study_name" placeholder="晚期非小细胞肺癌患者免疫联合治疗临床研究" required /></label>
      <label className="field"><span>适应症</span><input className="input" name="indication" placeholder="NSCLC" /></label>
      <label className="field"><span>研究阶段</span><input className="input" name="phase" placeholder="II期" /></label>
      <label className="field"><span>申办方</span><input className="input" name="sponsor" placeholder="KeyMedBio" /></label>
      <div className="field form-actions"><span>&nbsp;</span><button className="btn btn-primary" type="submit">创建项目</button></div>
    </form>
  )
}

function ProjectWorkspace({
  project,
  subjects,
  criteria,
  files,
  onCreateSubject,
  onCreateCriterion,
  onUpdatePrompt,
  onUploadProjectFile,
  onGenerateCriteria,
  onConfirmCriterion,
  onConfirmAllCriteria,
}: {
  readonly project: Project | null
  readonly subjects: Subject[]
  readonly criteria: Criterion[]
  readonly files: UploadedFile[]
  readonly onCreateSubject: (form: { subject_no: string; site_name?: string; gender?: string; age?: number; diagnosis?: string }) => Promise<void>
  readonly onCreateCriterion: (form: { criterion_code: string; criterion_type: "inclusion" | "exclusion"; criterion_text: string; ai_instruction?: string; sort_order: number }) => Promise<void>
  readonly onUpdatePrompt: (aiPrompt: string) => Promise<void>
  readonly onUploadProjectFile: (file: File, fileType: string) => Promise<void>
  readonly onGenerateCriteria: () => Promise<void>
  readonly onConfirmCriterion: (criterionId: string) => Promise<void>
  readonly onConfirmAllCriteria: (criterionIds: readonly string[]) => Promise<void>
}) {
  const [isSubjectOpen, setIsSubjectOpen] = useState(false)
  const [isCriterionOpen, setIsCriterionOpen] = useState(false)
  const [isFileUploadOpen, setIsFileUploadOpen] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isConfirmingAll, setIsConfirmingAll] = useState(false)
  const hasProtocolFile = files.some((file) => file.file_scope === "project_protocol")
  const inclusionCount = criteria.filter((item) => item.criterion_type === "inclusion").length
  const exclusionCount = criteria.filter((item) => item.criterion_type === "exclusion").length
  const draftCriterionIds = criteria.filter((item) => item.review_status === "draft").map((item) => item.id)

  return (
    <>
      <PageHeader
        kicker={project?.project_no ?? "Project"}
        title={project?.study_name ?? "项目详情"}
        description="配置项目入排标准、上传方案文件、管理候选受试者，并启动后续 AI 初筛闭环。"
        actions={<button className="btn btn-secondary" type="button" onClick={() => navigate("/projects")}>返回项目列表</button>}
      />
      <section className="grid-4">
        <MetricCard label="受试者" value={subjects.length} />
        <MetricCard label="入选标准" tone="success" value={inclusionCount} />
        <MetricCard label="排除标准" tone="danger" value={exclusionCount} />
        <MetricCard label="项目文件" tone="info" value={files.length} />
      </section>
      <DataCard>
        <CardTitle
          title="候选受试者"
          meta="资料上传、初筛状态和总体建议"
          actions={<button className="btn btn-primary" type="button" onClick={() => setIsSubjectOpen(true)}>新增受试者</button>}
        />
        {subjects.length === 0 ? <EmptyState>暂无受试者。</EmptyState> : <SubjectsTable subjects={subjects} />}
      </DataCard>
      <DataCard>
        <CardTitle
          title="项目方案文件"
          meta="protocol / informed consent"
          actions={<button className="btn btn-primary" type="button" onClick={() => setIsFileUploadOpen(true)}>上传项目文件</button>}
        />
        <FilesTable files={files} />
      </DataCard>
      <DataCard>
        <CardTitle
          title="入排标准"
          meta="AI 判断配置"
          actions={
            <>
              <button
                className="btn btn-secondary"
                type="button"
                disabled={isGenerating || !hasProtocolFile}
                title={hasProtocolFile ? "" : "请先上传研究方案文件"}
                onClick={async () => {
                  setIsGenerating(true)
                  try {
                    await onGenerateCriteria()
                  } finally {
                    setIsGenerating(false)
                  }
                }}
              >
                {isGenerating ? "AI 解析方案中…" : "AI 生成入排标准"}
              </button>
              {draftCriterionIds.length > 0 ? (
                <button
                  className="btn btn-primary"
                  type="button"
                  disabled={isConfirmingAll}
                  onClick={async () => {
                    setIsConfirmingAll(true)
                    try {
                      await onConfirmAllCriteria(draftCriterionIds)
                    } finally {
                      setIsConfirmingAll(false)
                    }
                  }}
                >
                  {isConfirmingAll ? "确认中…" : `全部采用（${draftCriterionIds.length}）`}
                </button>
              ) : null}
              <button className="btn btn-primary" type="button" onClick={() => setIsCriterionOpen(true)}>新增入排标准</button>
            </>
          }
        />
        {criteria.length === 0 ? <EmptyState>暂无入排标准。上传研究方案后可点击「AI 生成入排标准」自动解析。</EmptyState> : <CriteriaTable criteria={criteria} onConfirmCriterion={onConfirmCriterion} />}
      </DataCard>
      <DataCard>
        <CardTitle title="项目级 AI 提示词" meta="控制整体判断原则和证据引用要求" />
        <ProjectPromptForm aiPrompt={project?.ai_prompt ?? ""} onSubmit={onUpdatePrompt} />
      </DataCard>
      <Modal isOpen={isSubjectOpen} title="新增受试者" onClose={() => setIsSubjectOpen(false)}>
        <SubjectForm
          onSubmit={async (form) => {
            await onCreateSubject(form)
            setIsSubjectOpen(false)
          }}
        />
      </Modal>
      <Modal isOpen={isCriterionOpen} title="新增入排标准" onClose={() => setIsCriterionOpen(false)}>
        <CriterionForm
          sortOrder={criteria.length + 1}
          onSubmit={async (form) => {
            await onCreateCriterion(form)
            setIsCriterionOpen(false)
          }}
        />
      </Modal>
      <Modal isOpen={isFileUploadOpen} title="上传项目文件" onClose={() => setIsFileUploadOpen(false)}>
        <FileUpload
          onSubmit={async (file, fileType) => {
            await onUploadProjectFile(file, fileType)
            setIsFileUploadOpen(false)
          }}
        />
      </Modal>
    </>
  )
}

function ProjectPromptForm({
  aiPrompt,
  onSubmit,
}: {
  readonly aiPrompt: string
  readonly onSubmit: (aiPrompt: string) => Promise<void>
}) {
  return (
    <form
      className="card-pad field"
      onSubmit={(event) => {
        event.preventDefault()
        const form = new FormData(event.currentTarget)
        void onSubmit(String(form.get("ai_prompt") ?? ""))
      }}
    >
      <label className="field">
        <span>AI 判断原则</span>
        <textarea
          className="textarea"
          name="ai_prompt"
          defaultValue={aiPrompt}
          placeholder="请基于受试者上传的原始资料逐条判断入排标准；证据不足时标记资料不足或需人工确认；所有判断必须引用来源文件、页码和原文片段。"
        />
      </label>
      <div className="toolbar">
        <button className="btn btn-primary" type="submit">保存 AI 提示词</button>
      </div>
    </form>
  )
}

function SubjectForm({ onSubmit }: { readonly onSubmit: (form: { subject_no: string; site_name?: string; gender?: string; age?: number; diagnosis?: string }) => Promise<void> }) {
  const [busy, setBusy] = useState(false)

  return (
    <form className="form-grid card-pad" onSubmit={(event) => {
      event.preventDefault()
      if (busy) {
        return
      }
      const formElement = event.currentTarget
      const form = new FormData(formElement)
      const ageValue = String(form.get("age") ?? "")
      setBusy(true)
      void onSubmit({
        subject_no: String(form.get("subject_no") ?? ""),
        site_name: String(form.get("site_name") ?? ""),
        gender: String(form.get("gender") ?? ""),
        age: ageValue === "" ? undefined : Number(ageValue),
        diagnosis: String(form.get("diagnosis") ?? ""),
      })
        .then(() => formElement.reset())
        .finally(() => setBusy(false))
    }}>
      <label className="field"><span>受试者编号</span><input className="input" name="subject_no" placeholder="S-001" required /></label>
      <label className="field"><span>中心</span><input className="input" name="site_name" placeholder="郑州中心" /></label>
      <label className="field"><span>性别</span><select className="select" name="gender" defaultValue=""><option value="">未填</option><option value="男">男</option><option value="女">女</option></select></label>
      <label className="field"><span>年龄</span><input className="input" name="age" type="number" min="0" /></label>
      <label className="field wide"><span>诊断</span><input className="input" name="diagnosis" placeholder="晚期非小细胞肺癌" /></label>
      <div className="field form-actions"><span>&nbsp;</span><button className="btn btn-primary" type="submit" disabled={busy}>{busy ? "创建中…" : "新增受试者"}</button></div>
    </form>
  )
}

function CriterionForm({ sortOrder, onSubmit }: { readonly sortOrder: number; readonly onSubmit: (form: { criterion_code: string; criterion_type: "inclusion" | "exclusion"; criterion_text: string; ai_instruction?: string; sort_order: number }) => Promise<void> }) {
  return (
    <form className="form-grid card-pad" onSubmit={(event) => {
      event.preventDefault()
      const form = new FormData(event.currentTarget)
      const criterionType = String(form.get("criterion_type") ?? "inclusion") === "exclusion" ? "exclusion" : "inclusion"
      void onSubmit({
        criterion_code: String(form.get("criterion_code") ?? ""),
        criterion_type: criterionType,
        criterion_text: String(form.get("criterion_text") ?? ""),
        ai_instruction: String(form.get("ai_instruction") ?? ""),
        sort_order: sortOrder,
      }).then(() => event.currentTarget.reset())
    }}>
      <label className="field"><span>标准编号</span><input className="input" name="criterion_code" placeholder="I-01" required /></label>
      <label className="field"><span>类型</span><select className="select" name="criterion_type"><option value="inclusion">入选</option><option value="exclusion">排除</option></select></label>
      <label className="field wide"><span>标准文本</span><textarea className="textarea" name="criterion_text" required placeholder="年龄 18–75 周岁，男女不限。" /></label>
      <label className="field wide"><span>AI 判断提示</span><textarea className="textarea" name="ai_instruction" placeholder="优先从病历首页、人口学信息或入院记录中提取年龄。" /></label>
      <div className="field form-actions"><span>&nbsp;</span><button className="btn btn-primary" type="submit">新增标准</button></div>
    </form>
  )
}

function FileUpload({ onSubmit }: { readonly onSubmit: (file: File, fileType: string) => Promise<void> }) {
  return (
    <form className="toolbar card-pad compact-form" onSubmit={(event) => {
      event.preventDefault()
      const form = new FormData(event.currentTarget)
      const file = form.get("file")
      if (file instanceof File && file.size > 0) {
        void onSubmit(file, String(form.get("file_type") ?? "protocol")).then(() => event.currentTarget.reset())
      }
    }}>
      <input className="input" name="file" type="file" required />
      <select className="select" name="file_type" defaultValue="protocol">
        <option value="protocol">研究方案</option>
        <option value="medical_record">病历</option>
        <option value="lab_report">检验报告</option>
        <option value="imaging_report">影像报告</option>
        <option value="other">其他</option>
      </select>
      <button className="btn btn-secondary" type="submit">上传文件</button>
    </form>
  )
}

function SubjectsTable({ subjects }: { readonly subjects: Subject[] }) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead><tr><th>受试者</th><th>中心</th><th>年龄/性别</th><th>诊断</th><th>素材</th><th>AI 初筛状态</th><th>总体建议</th><th>操作</th></tr></thead>
        <tbody>{subjects.map((item) => (
          <tr key={item.id}>
            <td className="mono">{item.subject_no}</td><td>{item.site_name ?? "—"}</td><td>{item.age ?? "—"} / {item.gender ?? "—"}</td><td>{item.diagnosis ?? "—"}</td><td>{item.material_count}</td><td><span className={badgeClass(item.screening_status)}>{item.screening_status}</span></td><td><span className={badgeClass(item.overall_result)}>{resultLabel(item.overall_result)}</span></td><td><button className="btn btn-primary" type="button" onClick={() => navigate(`/subjects/${item.id}`)}>查看匹配</button></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

function CriteriaTable({
  criteria,
  onConfirmCriterion,
}: {
  readonly criteria: Criterion[]
  readonly onConfirmCriterion?: (criterionId: string) => Promise<void>
}) {
  const [confirmingIds, setConfirmingIds] = useState<readonly string[]>([])

  const handleConfirm = async (criterionId: string) => {
    if (onConfirmCriterion === undefined) {
      return
    }
    setConfirmingIds((current) => [...current, criterionId])
    try {
      await onConfirmCriterion(criterionId)
    } catch {
      setConfirmingIds((current) => current.filter((id) => id !== criterionId))
    }
  }

  return (
    <div className="criteria-list card-pad">
      {criteria.map((item) => {
        const isDraft = item.review_status === "draft"
        const isConfirming = confirmingIds.includes(item.id)
        return (
          <article className="criteria-item" key={item.id}>
            <div className="toolbar">
              <span className={item.criterion_type === "inclusion" ? "tag tag-success" : "tag tag-danger"}>{item.criterion_code} · {item.criterion_type === "inclusion" ? "入选" : "排除"}</span>
              {isDraft ? <span className="tag tag-warning">AI 草稿</span> : null}
            </div>
            <p>{item.criterion_text}</p>
            <small className="muted">{item.ai_instruction ?? "未配置标准级 AI 提示"}</small>
            {isDraft && onConfirmCriterion !== undefined ? (
              <div className="toolbar">
                {isConfirming ? (
                  <span className="tag tag-info">确认中…</span>
                ) : (
                  <button className="btn btn-primary" type="button" onClick={() => void handleConfirm(item.id)}>确认采用</button>
                )}
              </div>
            ) : null}
          </article>
        )
      })}
    </div>
  )
}

function FilesTable({ files }: { readonly files: UploadedFile[] }) {
  if (files.length === 0) {
    return <EmptyState>暂无文件。</EmptyState>
  }
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead><tr><th>文件名</th><th>分类</th><th>范围</th><th>页数</th><th>解析</th><th>上传时间</th></tr></thead>
        <tbody>{files.map((file) => (
          <tr key={file.id}><td>{file.file_name}</td><td>{file.file_type}</td><td>{file.file_scope}</td><td>{file.page_count ?? "—"}</td><td><span className={badgeClass(file.parse_status)}>{file.parse_status}</span></td><td>{new Date(file.uploaded_at).toLocaleString()}</td></tr>
        ))}</tbody>
      </table>
    </div>
  )
}

function SubjectScreeningPage({
  project,
  subject,
  files,
  evaluations,
  selectedEvaluation,
  onSelectEvaluation,
  onStartScreening,
  onExport,
  onManualReview,
  onUploadSubjectFile,
}: {
  readonly project: Project | null
  readonly subject: Subject | null
  readonly files: UploadedFile[]
  readonly evaluations: Evaluation[]
  readonly selectedEvaluation: EvaluationDetail | null
  readonly onSelectEvaluation: (evaluationId: string) => Promise<void>
  readonly onStartScreening: () => Promise<void>
  readonly onExport: () => Promise<void>
  readonly onManualReview: (
    evaluationId: string,
    manualResult: string,
    manualComment: string,
    reviewStatus: "reviewed" | "modified",
  ) => Promise<void>
  readonly onUploadSubjectFile: (file: File, fileType: string) => Promise<void>
}) {
  const averageConfidence = useMemo(() => {
    const scores = evaluations.map((item) => item.confidence_score).filter((item): item is number => typeof item === "number")
    if (scores.length === 0) {
      return 0
    }
    return Math.round(scores.reduce((sum, item) => sum + item, 0) / scores.length)
  }, [evaluations])
  const reviewCount = evaluations.filter((item) => item.ai_result === "manual_review" || item.ai_result === "insufficient_data").length

  return (
    <>
      <PageHeader
        kicker={subject?.subject_no ?? "Subject"}
        title="受试者 AI 初筛建议"
        description={`${project?.study_name ?? "未返回项目"} · ${subject?.diagnosis ?? "未填写诊断"}`}
        actions={<><button className="btn btn-secondary" type="button" onClick={() => project?.id === undefined ? navigate("/projects") : navigate(`/projects/${project.id}`)}>返回项目</button><button className="btn btn-secondary" type="button" onClick={() => void onExport()}>导出 JSON 报告</button><button className="btn btn-primary" type="button" onClick={() => void onStartScreening()}>启动 AI 初筛</button></>}
      />
      <section className="grid-4">
        <MetricCard label="总体建议" tone="warning" value={resultLabel(subject?.overall_result)} />
        <MetricCard label="平均置信度" tone="info" value={`${averageConfidence}%`} />
        <MetricCard label="标准级判断" tone="success" value={evaluations.length} />
        <MetricCard label="待复核/资料不足" tone="warning" value={reviewCount} />
      </section>
      <DataCard>
        <CardTitle title="上传受试者资料" meta="medical_record / lab_report / imaging_report" />
        <FileUpload onSubmit={onUploadSubjectFile} />
        <FilesTable files={files} />
      </DataCard>
      <section className="screening-grid">
        <div>
          <DataCard>
            <CardTitle title="标准级判断" meta="AI 初筛建议不是最终医学决定" />
            {evaluations.length === 0 ? <EmptyState>该受试者尚未进行 AI 初筛，或后端尚未生成评价结果。</EmptyState> : (
              <div className="table-wrap"><table className="data-table"><thead><tr><th>标准</th><th>AI 初筛建议</th><th>置信度</th><th>证据数</th><th>依据说明</th><th>操作</th></tr></thead><tbody>{evaluations.map((evaluation) => (
                <tr key={evaluation.id}><td><span className="mono">{evaluation.criterion_code}</span><p>{evaluation.criterion_text}</p></td><td><span className={badgeClass(evaluation.ai_result)}>{resultLabel(evaluation.ai_result)}</span></td><td><div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={evaluation.confidence_score ?? 0}><span style={{ width: `${evaluation.confidence_score ?? 0}%` }} /></div><p className="caption">{evaluation.confidence_score ?? 0}%</p></td><td>{evaluation.citation_count}</td><td>{evaluation.ai_rationale ?? "—"}</td><td><button className="btn btn-secondary" type="button" onClick={() => void onSelectEvaluation(evaluation.id)}>查看证据</button></td></tr>
              ))}</tbody></table></div>
            )}
          </DataCard>
        </div>
        <EvidencePanel evaluation={selectedEvaluation} onManualReview={onManualReview} />
      </section>
    </>
  )
}

function EvidencePanel({
  evaluation,
  onManualReview,
}: {
  readonly evaluation: EvaluationDetail | null
  readonly onManualReview: (
    evaluationId: string,
    manualResult: string,
    manualComment: string,
    reviewStatus: "reviewed" | "modified",
  ) => Promise<void>
}) {
  if (evaluation === null) {
    return <aside className="drawer"><div className="drawer-header"><span className="eyebrow">Evidence</span><h2>证据详情</h2><p className="muted">选择一条标准级判断查看原文引用。</p></div></aside>
  }
  return (
    <aside className="drawer">
      <div className="drawer-header"><span className={badgeClass(evaluation.ai_result)}>{resultLabel(evaluation.ai_result)}</span><h2>{evaluation.criterion_code} 证据详情</h2><p className="muted">{evaluation.criterion_text}</p></div>
      <div className="drawer-body">
        <div className="evidence-block"><strong>AI 依据说明</strong><p>{evaluation.ai_rationale ?? "—"}</p></div>
        {evaluation.citations.length === 0 ? <EmptyState>该判断暂无证据引用。</EmptyState> : evaluation.citations.map((citation, index) => (
          <div className="evidence-block" key={`${citation.chunk_id ?? citation.file_id ?? "citation"}-${index}`}>
            <span className="tag tag-info">{citation.file_name ?? "未知文件"} · 第 {citation.page_no ?? "—"} 页</span>
            <p><mark>{citation.quoted_text ?? "未返回原文摘录"}</mark></p>
            <p className="muted">{citation.extracted_fact ?? "未返回抽取事实"}</p>
            <small>{citation.relevance_explanation ?? "未返回关联解释"}</small>
          </div>
        ))}
      </div>
      <form
        className="manual-review-form"
        onSubmit={(event) => {
          event.preventDefault()
          const form = new FormData(event.currentTarget)
          const manualResult = String(form.get("manual_result") ?? evaluation.ai_result)
          const manualComment = String(form.get("manual_comment") ?? "")
          const reviewStatus = manualResult === evaluation.ai_result ? "reviewed" : "modified"
          void onManualReview(evaluation.id, manualResult, manualComment, reviewStatus)
        }}
      >
        <label className="field">
          <span>人工复核结论</span>
          <select className="select" name="manual_result" defaultValue={evaluation.manual_result ?? evaluation.ai_result}>
            <option value="pass">证据支持</option>
            <option value="fail">未通过</option>
            <option value="exclusion_hit">命中排除</option>
            <option value="exclusion_not_hit">未命中排除</option>
            <option value="insufficient_data">资料不足</option>
            <option value="manual_review">需人工确认</option>
          </select>
        </label>
        <label className="field">
          <span>复核意见</span>
          <textarea
            className="textarea"
            name="manual_comment"
            defaultValue={evaluation.manual_comment ?? ""}
            placeholder="记录 CRC / 研究者复核意见，用于审计追踪。"
          />
        </label>
        <div className="drawer-footer">
          <button className="btn btn-primary" type="submit">保存人工复核</button>
        </div>
      </form>
    </aside>
  )
}

function AuditPage({ logs }: { readonly logs: AuditLog[] }) {
  return (
    <>
      <PageHeader kicker="Audit" title="审计日志" description="查看文件上传、初筛运行、人工复核和导出等关键操作记录。" />
      <DataCard>
        <CardTitle title="操作记录" meta={`${logs.length} 条`} />
        {logs.length === 0 ? <EmptyState>暂无审计日志，或当前用户没有 admin 权限。</EmptyState> : (
          <div className="table-wrap"><table className="data-table"><thead><tr><th>动作</th><th>目标</th><th>项目</th><th>受试者</th><th>用户</th><th>时间</th></tr></thead><tbody>{logs.map((item) => (
            <tr key={item.id}><td className="mono">{item.action_type}</td><td>{item.target_type} / {item.target_id}</td><td>{item.project_id ?? "—"}</td><td>{item.subject_id ?? "—"}</td><td>{item.user_id ?? "—"}</td><td>{item.created_at === null || item.created_at === undefined ? "—" : new Date(item.created_at).toLocaleString()}</td></tr>
          ))}</tbody></table></div>
        )}
      </DataCard>
    </>
  )
}
