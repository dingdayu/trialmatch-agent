# TrialMatch AI 接口文档

版本：v0.1.0
系统名称：TrialMatch AI / 研筛通
接口前缀：`/api/v1`
认证方式：JWT Bearer Token
默认数据格式：`application/json`
文件上传格式：`multipart/form-data`

---

## 1. 通用约定

### 1.1 Base URL

```text
/api/v1
```

示例：

```text
POST /api/v1/auth/login
GET  /api/v1/projects
```

---

### 1.2 请求头

除登录接口外，其他接口默认需要携带 Token。

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

文件上传接口使用：

```http
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

---

### 1.3 通用响应结构

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "req_202606270001"
}
```

失败响应：

```json
{
  "code": 40001,
  "message": "invalid request parameter",
  "data": null,
  "request_id": "req_202606270002"
}
```

---

### 1.4 分页响应结构

列表接口统一支持分页。

请求参数：

| 参数        |      类型 | 必填 | 说明         |
| --------- | ------: | -: | ---------- |
| page      | integer |  否 | 页码，默认 1    |
| page_size | integer |  否 | 每页数量，默认 20 |
| keyword   |  string |  否 | 搜索关键字      |

响应结构：

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 120
}
```

---

### 1.5 通用错误码

|  code | 说明            |
| ----: | ------------- |
|     0 | 成功            |
| 40001 | 请求参数错误        |
| 40002 | 数据校验失败        |
| 40101 | 未登录或 Token 无效 |
| 40301 | 无权限           |
| 40401 | 资源不存在         |
| 40901 | 数据冲突，例如项目编号重复 |
| 50001 | 服务内部错误        |
| 50002 | AI 分析任务失败     |
| 50003 | 文件解析失败        |

---

## 2. 枚举定义

### 2.1 用户角色 role

| 值               | 说明    |
| --------------- | ----- |
| admin           | 系统管理员 |
| project_manager | 项目管理员 |
| crc             | CRC   |
| viewer          | 只读用户  |

---

### 2.2 项目状态 project.status

| 值           | 说明  |
| ----------- | --- |
| draft       | 草稿  |
| configuring | 配置中 |
| screening   | 筛选中 |
| paused      | 已暂停 |
| completed   | 已完成 |

---

### 2.3 标准类型 criterion_type

| 值         | 说明   |
| --------- | ---- |
| inclusion | 入选标准 |
| exclusion | 排除标准 |

---

### 2.4 文件归属 file_scope

| 值                | 说明     |
| ---------------- | ------ |
| subject_data     | 受试者资料  |
| project_protocol | 项目方案文件 |

---

### 2.5 文件类型 file_type

| 值                 | 说明   |
| ----------------- | ---- |
| protocol          | 项目方案 |
| medical_record    | 病例   |
| lab_report        | 检验报告 |
| exam_report       | 检查报告 |
| imaging_report    | 影像报告 |
| pathology_report  | 病理报告 |
| discharge_summary | 出院记录 |
| informed_consent  | 知情同意 |
| other             | 其他   |

---

### 2.6 文件解析状态 parse_status

| 值       | 说明   |
| ------- | ---- |
| pending | 待解析  |
| parsing | 解析中  |
| parsed  | 已解析  |
| failed  | 解析失败 |

---

### 2.7 AI 初筛状态 screening_status

| 值           | 说明    |
| ----------- | ----- |
| not_started | 未开始   |
| parsing     | 解析中   |
| matching    | 匹配中   |
| need_review | 待人工确认 |
| completed   | 已完成   |
| failed      | 失败    |

---

### 2.8 受试者总体结论 overall_result

| 值                 | 说明    |
| ----------------- | ----- |
| recommended       | 建议入组  |
| excluded          | 疑似排除  |
| insufficient_data | 资料不足  |
| manual_review     | 需人工确认 |

---

### 2.9 AI 分析任务状态 screening_runs.status

| 值         | 说明  |
| --------- | --- |
| queued    | 排队中 |
| running   | 运行中 |
| completed | 已完成 |
| failed    | 失败  |

---

### 2.10 入选标准 AI 结果 ai_result

| 值                 | 说明    |
| ----------------- | ----- |
| pass              | 通过    |
| fail              | 不通过   |
| insufficient_data | 资料不足  |
| manual_review     | 需人工确认 |

---

### 2.11 排除标准 AI 结果 ai_result

| 值                 | 说明    |
| ----------------- | ----- |
| exclusion_hit     | 命中排除  |
| exclusion_not_hit | 未命中排除 |
| insufficient_data | 资料不足  |
| manual_review     | 需人工确认 |

---

## 3. 用户与认证接口

---

### 3.1 登录

```http
POST /auth/login
```

请求体：

```json
{
  "username": "crc001",
  "password": "123456"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "username": "crc001",
      "display_name": "CRC 用户",
      "role": "crc",
      "email": "crc001@example.com"
    }
  },
  "request_id": "req_001"
}
```

---

### 3.2 获取当前用户信息

```http
GET /auth/me
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "crc001",
    "display_name": "CRC 用户",
    "role": "crc",
    "email": "crc001@example.com",
    "status": "active"
  },
  "request_id": "req_002"
}
```

---

### 3.3 刷新 Token

```http
POST /auth/refresh
```

请求体：

```json
{
  "refresh_token": "jwt_refresh_token"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "new_jwt_access_token",
    "refresh_token": "new_jwt_refresh_token",
    "expires_in": 7200
  },
  "request_id": "req_003"
}
```

---

### 3.4 退出登录

```http
POST /auth/logout
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true,
  "request_id": "req_004"
}
```

---

## 4. 项目接口

---

### 4.1 获取项目列表

```http
GET /projects
```

查询参数：

| 参数        |      类型 | 必填 | 说明              |
| --------- | ------: | -: | --------------- |
| page      | integer |  否 | 页码              |
| page_size | integer |  否 | 每页数量            |
| keyword   |  string |  否 | 搜索项目编号、研究名称、适应症 |
| status    |  string |  否 | 项目状态            |
| phase     |  string |  否 | 研究阶段            |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "project_no": "KM-CRC-2026-001",
        "study_name": "晚期非小细胞肺癌患者免疫联合治疗临床研究",
        "study_short_name": "NSCLC-IO-001",
        "indication": "NSCLC",
        "phase": "II期",
        "sponsor": "KeyMedBio",
        "status": "screening",
        "site_count": 3,
        "subject_count": 24,
        "completed_screening_count": 18,
        "pending_review_count": 6,
        "updated_at": "2026-06-27T10:30:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  },
  "request_id": "req_101"
}
```

---

### 4.2 创建项目

```http
POST /projects
```

请求体：

```json
{
  "project_no": "KM-CRC-2026-001",
  "study_name": "晚期非小细胞肺癌患者免疫联合治疗临床研究",
  "study_short_name": "NSCLC-IO-001",
  "indication": "NSCLC",
  "phase": "II期",
  "sponsor": "KeyMedBio",
  "principal_investigator": "张教授",
  "project_manager": "李经理",
  "status": "configuring",
  "description": "用于晚期非小细胞肺癌患者的 AI 辅助初筛项目",
  "ai_prompt": "请基于受试者原始资料逐条判断入排标准，不得凭空推断。"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "project_no": "KM-CRC-2026-001"
  },
  "request_id": "req_102"
}
```

---

### 4.3 获取项目详情

```http
GET /projects/{project_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "project_no": "KM-CRC-2026-001",
    "study_name": "晚期非小细胞肺癌患者免疫联合治疗临床研究",
    "study_short_name": "NSCLC-IO-001",
    "indication": "NSCLC",
    "phase": "II期",
    "sponsor": "KeyMedBio",
    "principal_investigator": "张教授",
    "project_manager": "李经理",
    "status": "screening",
    "description": "用于晚期非小细胞肺癌患者的 AI 辅助初筛项目",
    "ai_prompt": "请基于受试者原始资料逐条判断入排标准，不得凭空推断。",
    "created_at": "2026-06-20T08:00:00Z",
    "updated_at": "2026-06-27T10:30:00Z"
  },
  "request_id": "req_103"
}
```

---

### 4.4 更新项目

```http
PUT /projects/{project_id}
```

请求体：

```json
{
  "study_name": "晚期非小细胞肺癌患者免疫联合治疗临床研究",
  "study_short_name": "NSCLC-IO-001",
  "indication": "NSCLC",
  "phase": "II期",
  "sponsor": "KeyMedBio",
  "principal_investigator": "张教授",
  "project_manager": "李经理",
  "status": "screening",
  "description": "更新后的项目描述",
  "ai_prompt": "请基于受试者上传资料逐条判断入排标准，并提供引用来源。"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true,
  "request_id": "req_104"
}
```

---

### 4.5 删除项目

```http
DELETE /projects/{project_id}
```

说明：建议使用软删除。

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true,
  "request_id": "req_105"
}
```

---

## 5. 入排标准接口

---

### 5.1 获取项目入排标准列表

```http
GET /projects/{project_id}/criteria
```

查询参数：

| 参数             |      类型 | 必填 | 说明                    |
| -------------- | ------: | -: | --------------------- |
| criterion_type |  string |  否 | inclusion / exclusion |
| is_active      | boolean |  否 | 是否启用                  |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "project_id": 1,
      "criterion_code": "I-01",
      "criterion_type": "inclusion",
      "criterion_text": "年龄 18–75 周岁，男女不限。",
      "criterion_explanation": "判断受试者年龄是否在 18 到 75 周岁之间。",
      "ai_instruction": "优先从身份证、病历首页、入院记录中提取出生日期或年龄。",
      "required_fields": ["age", "birth_date"],
      "sort_order": 1,
      "is_active": true
    }
  ],
  "request_id": "req_201"
}
```

---

### 5.2 新增入排标准

```http
POST /projects/{project_id}/criteria
```

请求体：

```json
{
  "criterion_code": "I-01",
  "criterion_type": "inclusion",
  "criterion_text": "年龄 18–75 周岁，男女不限。",
  "criterion_explanation": "判断受试者年龄是否在 18 到 75 周岁之间。",
  "ai_instruction": "优先从身份证、病历首页、入院记录中提取出生日期或年龄。",
  "required_fields": ["age", "birth_date"],
  "sort_order": 1,
  "is_active": true
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1
  },
  "request_id": "req_202"
}
```

---

### 5.3 获取单条入排标准

```http
GET /criteria/{criterion_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "project_id": 1,
    "criterion_code": "I-01",
    "criterion_type": "inclusion",
    "criterion_text": "年龄 18–75 周岁，男女不限。",
    "criterion_explanation": "判断受试者年龄是否在 18 到 75 周岁之间。",
    "ai_instruction": "优先从身份证、病历首页、入院记录中提取出生日期或年龄。",
    "required_fields": ["age", "birth_date"],
    "sort_order": 1,
    "is_active": true
  },
  "request_id": "req_203"
}
```

---

### 5.4 更新入排标准

```http
PUT /criteria/{criterion_id}
```

请求体：

```json
{
  "criterion_code": "I-01",
  "criterion_text": "年龄 18–75 周岁，男女不限。",
  "criterion_explanation": "判断年龄是否满足方案要求。",
  "ai_instruction": "如仅有出生年份，可根据筛选日期估算年龄，并标记需人工确认。",
  "required_fields": ["age", "birth_date", "screening_date"],
  "sort_order": 1,
  "is_active": true
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true,
  "request_id": "req_204"
}
```

---

### 5.5 删除入排标准

```http
DELETE /criteria/{criterion_id}
```

说明：建议软删除或设置 `is_active=false`。

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true,
  "request_id": "req_205"
}
```

---

### 5.6 批量导入入排标准

```http
POST /projects/{project_id}/criteria/batch-import
```

请求体：

```json
{
  "criteria": [
    {
      "criterion_code": "I-01",
      "criterion_type": "inclusion",
      "criterion_text": "年龄 18–75 周岁，男女不限。",
      "criterion_explanation": "判断受试者年龄是否满足要求。",
      "ai_instruction": "从病例首页或入院记录中提取年龄。",
      "required_fields": ["age"],
      "sort_order": 1,
      "is_active": true
    },
    {
      "criterion_code": "E-01",
      "criterion_type": "exclusion",
      "criterion_text": "既往接受过同类免疫治疗。",
      "criterion_explanation": "判断是否存在既往同类免疫治疗史。",
      "ai_instruction": "重点查看既往治疗史、出院记录和病程记录。",
      "required_fields": ["treatment_history"],
      "sort_order": 101,
      "is_active": true
    }
  ]
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "created_count": 2,
    "failed_count": 0,
    "errors": []
  },
  "request_id": "req_206"
}
```

---

## 6. 受试者接口

---

### 6.1 获取项目下受试者列表

```http
GET /projects/{project_id}/subjects
```

查询参数：

| 参数               |      类型 | 必填 | 说明            |
| ---------------- | ------: | -: | ------------- |
| page             | integer |  否 | 页码            |
| page_size        | integer |  否 | 每页数量          |
| keyword          |  string |  否 | 搜索受试者编号、中心、诊断 |
| screening_status |  string |  否 | AI 初筛状态       |
| overall_result   |  string |  否 | 总体结论          |
| site_name        |  string |  否 | 中心名称          |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "project_id": 1,
        "subject_no": "S-001",
        "site_name": "郑州中心",
        "gender": "男",
        "age": 32,
        "birth_year": 1994,
        "diagnosis": "晚期非小细胞肺癌",
        "material_count": 4,
        "material_tags": ["病例", "病理报告", "检验报告", "影像报告"],
        "screening_status": "need_review",
        "overall_result": "manual_review",
        "inclusion_pass_count": 4,
        "exclusion_hit_count": 0,
        "pending_review_count": 2,
        "updated_at": "2026-06-27T10:30:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  },
  "request_id": "req_301"
}
```

---

### 6.2 新增受试者

```http
POST /projects/{project_id}/subjects
```

请求体：

```json
{
  "subject_no": "S-001",
  "site_name": "郑州中心",
  "gender": "男",
  "age": 32,
  "birth_year": 1994,
  "diagnosis": "晚期非小细胞肺癌",
  "remark": "初筛候选受试者"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "subject_no": "S-001"
  },
  "request_id": "req_302"
}
```

---

### 6.3 获取受试者详情

```http
GET /subjects/{subject_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "project_id": 1,
    "subject_no": "S-001",
    "site_name": "郑州中心",
    "gender": "男",
    "age": 32,
    "birth_year": 1994,
    "diagnosis": "晚期非小细胞肺癌",
    "material_count": 4,
    "screening_status": "need_review",
    "overall_result": "manual_review",
    "created_at": "2026-06-25T09:00:00Z",
    "updated_at": "2026-06-27T10:30:00Z"
  },
  "request_id": "req_303"
}
```

---

### 6.4 更新受试者

```http
PUT /subjects/{subject_id}
```

请求体：

```json
{
  "site_name": "郑州中心",
  "gender": "男",
  "age": 32,
  "birth_year": 1994,
  "diagnosis": "晚期非小细胞肺癌",
  "remark": "已补充病理报告"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true,
  "request_id": "req_304"
}
```

---

### 6.5 删除受试者

```http
DELETE /subjects/{subject_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true,
  "request_id": "req_305"
}
```

---

## 7. 文件上传与解析接口

---

### 7.1 上传项目方案文件

```http
POST /projects/{project_id}/files
```

请求类型：

```http
multipart/form-data
```

表单字段：

| 字段          | 类型      | 必填 | 说明                   |
| ----------- | ------- | -: | -------------------- |
| file        | file    |  是 | 上传文件                 |
| file_scope  | string  |  是 | 固定为 project_protocol |
| file_type   | string  |  是 | protocol             |
| description | string  |  否 | 文件说明                 |
| auto_parse  | boolean |  否 | 上传后是否自动解析            |

示例：

```text
file=<protocol.pdf>
file_scope=project_protocol
file_type=protocol
description=项目方案 V1.0
auto_parse=true
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 11,
    "file_name": "protocol_v1.0.pdf",
    "file_type": "protocol",
    "file_scope": "project_protocol",
    "parse_status": "pending"
  },
  "request_id": "req_401"
}
```

---

### 7.2 上传受试者资料文件

```http
POST /subjects/{subject_id}/files
```

请求类型：

```http
multipart/form-data
```

表单字段：

| 字段          | 类型      | 必填 | 说明                                          |
| ----------- | ------- | -: | ------------------------------------------- |
| file        | file    |  是 | 上传文件                                        |
| file_scope  | string  |  是 | 固定为 subject_data                            |
| file_type   | string  |  是 | medical_record / lab_report / exam_report 等 |
| description | string  |  否 | 文件说明                                        |
| auto_parse  | boolean |  否 | 上传后是否自动解析                                   |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 21,
    "file_name": "住院病历_2026-06-12.pdf",
    "file_type": "medical_record",
    "file_scope": "subject_data",
    "subject_id": 1,
    "parse_status": "pending"
  },
  "request_id": "req_402"
}
```

---

### 7.3 获取文件列表

```http
GET /files
```

查询参数：

| 参数           |      类型 | 必填 | 说明     |
| ------------ | ------: | -: | ------ |
| project_id   | integer |  否 | 项目 ID  |
| subject_id   | integer |  否 | 受试者 ID |
| file_scope   |  string |  否 | 文件归属   |
| file_type    |  string |  否 | 文件类型   |
| parse_status |  string |  否 | 解析状态   |
| page         | integer |  否 | 页码     |
| page_size    | integer |  否 | 每页数量   |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 21,
        "project_id": 1,
        "subject_id": 1,
        "file_name": "住院病历_2026-06-12.pdf",
        "file_path": "oss://trialmatch/subjects/S-001/住院病历_2026-06-12.pdf",
        "file_type": "medical_record",
        "file_scope": "subject_data",
        "mime_type": "application/pdf",
        "file_size": 2048000,
        "page_count": 8,
        "parse_status": "parsed",
        "uploaded_by": 1,
        "uploaded_at": "2026-06-27T09:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  },
  "request_id": "req_403"
}
```

---

### 7.4 获取文件详情

```http
GET /files/{file_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 21,
    "project_id": 1,
    "subject_id": 1,
    "file_name": "住院病历_2026-06-12.pdf",
    "file_type": "medical_record",
    "file_scope": "subject_data",
    "mime_type": "application/pdf",
    "file_size": 2048000,
    "page_count": 8,
    "parse_status": "parsed",
    "uploaded_at": "2026-06-27T09:00:00Z"
  },
  "request_id": "req_404"
}
```

---

### 7.5 触发文件解析

```http
POST /files/{file_id}/parse
```

请求体：

```json
{
  "force": false
}
```

字段说明：

| 字段    |      类型 | 必填 | 说明       |
| ----- | ------: | -: | -------- |
| force | boolean |  否 | 是否强制重新解析 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "file_id": 21,
    "parse_status": "parsing"
  },
  "request_id": "req_405"
}
```

---

### 7.6 获取文件解析片段

```http
GET /files/{file_id}/chunks
```

查询参数：

| 参数        |      类型 | 必填 | 说明   |
| --------- | ------: | -: | ---- |
| page_no   | integer |  否 | 页码   |
| keyword   |  string |  否 | 原文搜索 |
| page      | integer |  否 | 页码   |
| page_size | integer |  否 | 每页数量 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 301,
        "file_id": 21,
        "project_id": 1,
        "subject_id": 1,
        "page_no": 3,
        "chunk_index": 1,
        "content": "患者出生日期：1994-05-21，现年 32 岁。",
        "bbox": {
          "x": 120,
          "y": 260,
          "width": 430,
          "height": 40
        },
        "extracted_entities": {
          "birth_date": "1994-05-21",
          "age": 32
        }
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  },
  "request_id": "req_406"
}
```

---

### 7.7 删除文件

```http
DELETE /files/{file_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true,
  "request_id": "req_407"
}
```

---

## 8. AI 初筛任务接口

---

### 8.1 启动受试者 AI 初筛

```http
POST /subjects/{subject_id}/screening-runs
```

请求体：

```json
{
  "model_name": "gpt-5.5",
  "prompt_version": "v1",
  "force_reparse_files": false,
  "criteria_ids": [1, 2, 3, 101, 102]
}
```

字段说明：

| 字段                  |      类型 | 必填 | 说明                   |
| ------------------- | ------: | -: | -------------------- |
| model_name          |  string |  否 | 指定模型名称               |
| prompt_version      |  string |  否 | 提示词版本                |
| force_reparse_files | boolean |  否 | 是否重新解析文件             |
| criteria_ids        |   array |  否 | 指定要分析的标准；为空则分析全部启用标准 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "run_id": 1001,
    "run_no": "RUN-20260627-0001",
    "status": "queued"
  },
  "request_id": "req_501"
}
```

---

### 8.2 获取受试者 AI 初筛任务列表

```http
GET /subjects/{subject_id}/screening-runs
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1001,
      "project_id": 1,
      "subject_id": 1,
      "run_no": "RUN-20260627-0001",
      "status": "completed",
      "model_name": "gpt-5.5",
      "prompt_version": "v1",
      "started_at": "2026-06-27T10:00:00Z",
      "completed_at": "2026-06-27T10:03:00Z",
      "created_by": 1
    }
  ],
  "request_id": "req_502"
}
```

---

### 8.3 获取 AI 初筛任务详情

```http
GET /screening-runs/{run_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1001,
    "project_id": 1,
    "subject_id": 1,
    "run_no": "RUN-20260627-0001",
    "status": "completed",
    "model_name": "gpt-5.5",
    "prompt_version": "v1",
    "started_at": "2026-06-27T10:00:00Z",
    "completed_at": "2026-06-27T10:03:00Z",
    "error_message": null,
    "summary": {
      "overall_result": "manual_review",
      "score": 78,
      "inclusion_pass_count": 4,
      "inclusion_fail_count": 0,
      "inclusion_insufficient_count": 1,
      "exclusion_hit_count": 0,
      "exclusion_not_hit_count": 4,
      "exclusion_insufficient_count": 0,
      "manual_review_count": 1
    }
  },
  "request_id": "req_503"
}
```

---

### 8.4 重新运行 AI 初筛

```http
POST /screening-runs/{run_id}/rerun
```

请求体：

```json
{
  "model_name": "gpt-5.5",
  "prompt_version": "v2",
  "criteria_ids": []
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "run_id": 1002,
    "run_no": "RUN-20260627-0002",
    "status": "queued"
  },
  "request_id": "req_504"
}
```

---

## 9. 入排标准匹配结果接口

---

### 9.1 获取受试者最新匹配结果

```http
GET /subjects/{subject_id}/evaluations/latest
```

查询参数：

| 参数             |     类型 | 必填 | 说明                               |
| -------------- | -----: | -: | -------------------------------- |
| criterion_type | string |  否 | inclusion / exclusion            |
| ai_result      | string |  否 | AI 判断结果                          |
| review_status  | string |  否 | reviewed / unreviewed / modified |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "run_id": 1001,
    "subject": {
      "id": 1,
      "subject_no": "S-001",
      "site_name": "郑州中心",
      "gender": "男",
      "age": 32,
      "diagnosis": "晚期非小细胞肺癌"
    },
    "project": {
      "id": 1,
      "project_no": "KM-CRC-2026-001",
      "study_name": "晚期非小细胞肺癌患者免疫联合治疗临床研究"
    },
    "summary": {
      "overall_result": "manual_review",
      "score": 78,
      "ai_advice": "建议人工重点核查 E-03 排除标准和 I-03 ECOG 评分。",
      "inclusion_pass_count": 4,
      "inclusion_fail_count": 0,
      "inclusion_insufficient_count": 1,
      "exclusion_hit_count": 0,
      "exclusion_not_hit_count": 4,
      "manual_review_count": 1
    },
    "evaluations": [
      {
        "id": 9001,
        "criterion_id": 1,
        "criterion_code": "I-01",
        "criterion_type": "inclusion",
        "criterion_text": "年龄 18–75 周岁，男女不限。",
        "ai_result": "pass",
        "confidence_score": 96,
        "ai_rationale": "病例第 3 页显示患者出生日期为 1994-05-21，当前年龄 32 岁，满足 18–75 周岁的要求。",
        "citation_count": 1,
        "manual_result": null,
        "manual_comment": null,
        "review_status": "unreviewed"
      }
    ]
  },
  "request_id": "req_601"
}
```

---

### 9.2 获取某次任务的全部匹配结果

```http
GET /screening-runs/{run_id}/evaluations
```

响应结构同上，但不返回 `latest` 语义。

---

### 9.3 获取单条标准匹配详情

```http
GET /evaluations/{evaluation_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 9001,
    "run_id": 1001,
    "project_id": 1,
    "subject_id": 1,
    "criterion_id": 1,
    "criterion_code": "I-01",
    "criterion_type": "inclusion",
    "criterion_text": "年龄 18–75 周岁，男女不限。",
    "criterion_explanation": "判断受试者年龄是否在 18 到 75 周岁之间。",
    "ai_result": "pass",
    "confidence_score": 96,
    "ai_rationale": "病例第 3 页显示患者出生日期为 1994-05-21，当前年龄 32 岁，满足 18–75 周岁的要求。",
    "manual_result": null,
    "manual_comment": null,
    "reviewer_id": null,
    "reviewed_at": null,
    "citations": [
      {
        "id": 7001,
        "file_id": 21,
        "file_name": "住院病历_2026-06-12.pdf",
        "file_type": "medical_record",
        "page_no": 3,
        "chunk_id": 301,
        "quoted_text": "患者出生日期：1994-05-21，现年 32 岁。",
        "extracted_fact": "患者 1994-05-21 出生，现年 32 岁。",
        "relevance_explanation": "该证据支持患者年龄满足 18–75 周岁的入选标准。"
      }
    ]
  },
  "request_id": "req_603"
}
```

---

### 9.4 人工复核或改判单条标准

```http
PUT /evaluations/{evaluation_id}/manual-review
```

请求体：

```json
{
  "manual_result": "pass",
  "manual_comment": "人工复核病例首页，确认年龄满足入选标准。",
  "review_status": "reviewed"
}
```

字段说明：

| 字段             |     类型 | 必填 | 说明                  |
| -------------- | -----: | -: | ------------------- |
| manual_result  | string |  是 | 人工最终判断              |
| manual_comment | string |  否 | 人工复核意见              |
| review_status  | string |  是 | reviewed / modified |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluation_id": 9001,
    "review_status": "reviewed",
    "reviewed_at": "2026-06-27T11:00:00Z"
  },
  "request_id": "req_604"
}
```

---

### 9.5 批量人工确认

```http
POST /subjects/{subject_id}/evaluations/batch-review
```

请求体：

```json
{
  "evaluation_ids": [9001, 9002, 9003],
  "manual_comment": "批量确认 AI 判断结果无误。"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "reviewed_count": 3
  },
  "request_id": "req_605"
}
```

---

## 10. 引用来源接口

---

### 10.1 获取某条判断的引用来源

```http
GET /evaluations/{evaluation_id}/citations
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 7001,
      "evaluation_id": 9001,
      "file_id": 21,
      "file_name": "住院病历_2026-06-12.pdf",
      "file_type": "medical_record",
      "page_no": 3,
      "chunk_id": 301,
      "quoted_text": "患者出生日期：1994-05-21，现年 32 岁。",
      "extracted_fact": "患者 1994-05-21 出生，现年 32 岁。",
      "relevance_explanation": "该证据支持患者年龄满足 18–75 周岁的入选标准。"
    }
  ],
  "request_id": "req_701"
}
```

---

### 10.2 查看引用原文上下文

```http
GET /citations/{citation_id}/context
```

查询参数：

| 参数     |      类型 | 必填 | 说明           |
| ------ | ------: | -: | ------------ |
| before | integer |  否 | 向前返回几个 chunk |
| after  | integer |  否 | 向后返回几个 chunk |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "citation": {
      "id": 7001,
      "file_id": 21,
      "file_name": "住院病历_2026-06-12.pdf",
      "page_no": 3,
      "quoted_text": "患者出生日期：1994-05-21，现年 32 岁。"
    },
    "context_chunks": [
      {
        "chunk_id": 300,
        "page_no": 3,
        "content": "姓名：张某某，性别：男。"
      },
      {
        "chunk_id": 301,
        "page_no": 3,
        "content": "患者出生日期：1994-05-21，现年 32 岁。"
      },
      {
        "chunk_id": 302,
        "page_no": 3,
        "content": "入院诊断：晚期非小细胞肺癌。"
      }
    ]
  },
  "request_id": "req_702"
}
```

---

## 11. 项目统计接口

---

### 11.1 获取项目概览统计

```http
GET /projects/{project_id}/dashboard
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "project_id": 1,
    "subject_count": 24,
    "file_count": 96,
    "completed_screening_count": 18,
    "pending_review_count": 6,
    "recommended_count": 9,
    "excluded_count": 4,
    "insufficient_data_count": 5,
    "manual_review_count": 6,
    "failed_run_count": 1
  },
  "request_id": "req_801"
}
```

---

### 11.2 获取 AI 任务统计

```http
GET /projects/{project_id}/screening-runs/stats
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "queued_count": 1,
    "running_count": 2,
    "completed_count": 18,
    "failed_count": 1,
    "average_duration_seconds": 168
  },
  "request_id": "req_802"
}
```

---

## 12. 导出接口

---

### 12.1 导出受试者初筛报告

```http
POST /subjects/{subject_id}/export-report
```

请求体：

```json
{
  "run_id": 1001,
  "format": "pdf",
  "include_citations": true,
  "include_original_quotes": true
}
```

字段说明：

| 字段                      |      类型 | 必填 | 说明                |
| ----------------------- | ------: | -: | ----------------- |
| run_id                  | integer |  否 | 指定分析任务；为空则导出最新任务  |
| format                  |  string |  是 | pdf / docx / json |
| include_citations       | boolean |  否 | 是否包含引用来源          |
| include_original_quotes | boolean |  否 | 是否包含原文摘录          |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "export_task_id": "EXP-20260627-0001",
    "status": "queued"
  },
  "request_id": "req_901"
}
```

---

### 12.2 获取导出任务状态

```http
GET /export-tasks/{export_task_id}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "export_task_id": "EXP-20260627-0001",
    "status": "completed",
    "download_url": "/api/v1/export-tasks/EXP-20260627-0001/download",
    "created_at": "2026-06-27T11:00:00Z",
    "completed_at": "2026-06-27T11:01:00Z"
  },
  "request_id": "req_902"
}
```

---

### 12.3 下载导出文件

```http
GET /export-tasks/{export_task_id}/download
```

响应：

```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="S-001_screening_report.pdf"
```

---

## 13. 审计日志接口

---

### 13.1 获取审计日志

```http
GET /audit-logs
```

查询参数：

| 参数          |      类型 | 必填 | 说明     |
| ----------- | ------: | -: | ------ |
| project_id  | integer |  否 | 项目 ID  |
| subject_id  | integer |  否 | 受试者 ID |
| user_id     | integer |  否 | 用户 ID  |
| action_type |  string |  否 | 操作类型   |
| target_type |  string |  否 | 操作对象类型 |
| start_time  |  string |  否 | 开始时间   |
| end_time    |  string |  否 | 结束时间   |
| page        | integer |  否 | 页码     |
| page_size   | integer |  否 | 每页数量   |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "project_id": 1,
        "subject_id": 1,
        "user_id": 1,
        "user_name": "crc001",
        "action_type": "manual_review",
        "target_type": "criterion_evaluation",
        "target_id": 9001,
        "before_value": {
          "manual_result": null
        },
        "after_value": {
          "manual_result": "pass"
        },
        "created_at": "2026-06-27T11:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  },
  "request_id": "req_1001"
}
```

---

## 14. 推荐前端路由与接口对应关系

| 页面        | 前端路由                             | 主要接口                                                                          |
| --------- | -------------------------------- | ----------------------------------------------------------------------------- |
| 登录页       | `/login`                         | `POST /auth/login`                                                            |
| 项目列表      | `/projects`                      | `GET /projects`, `POST /projects`                                             |
| 项目详情 / 配置 | `/projects/:projectId/settings`  | `GET /projects/{id}`, `GET /projects/{id}/criteria`, `PUT /projects/{id}`     |
| 受试者列表     | `/projects/:projectId/subjects`  | `GET /projects/{id}/subjects`, `POST /projects/{id}/subjects`                 |
| 受试者匹配详情   | `/subjects/:subjectId/screening` | `GET /subjects/{id}/evaluations/latest`, `POST /subjects/{id}/screening-runs` |
| 文件管理      | `/files`                         | `GET /files`, `POST /subjects/{id}/files`, `POST /files/{id}/parse`           |
| 审计日志      | `/audit-logs`                    | `GET /audit-logs`                                                             |

---

## 15. 核心数据结构参考

### 15.1 Project

```json
{
  "id": 1,
  "project_no": "KM-CRC-2026-001",
  "study_name": "晚期非小细胞肺癌患者免疫联合治疗临床研究",
  "study_short_name": "NSCLC-IO-001",
  "indication": "NSCLC",
  "phase": "II期",
  "sponsor": "KeyMedBio",
  "principal_investigator": "张教授",
  "project_manager": "李经理",
  "status": "screening",
  "description": "项目描述",
  "ai_prompt": "项目级 AI 判断提示词",
  "created_by": 1,
  "created_at": "2026-06-20T08:00:00Z",
  "updated_at": "2026-06-27T10:30:00Z"
}
```

---

### 15.2 EligibilityCriterion

```json
{
  "id": 1,
  "project_id": 1,
  "criterion_code": "I-01",
  "criterion_type": "inclusion",
  "criterion_text": "年龄 18–75 周岁，男女不限。",
  "criterion_explanation": "判断受试者年龄是否在 18 到 75 周岁之间。",
  "ai_instruction": "优先从病历首页、入院记录中提取年龄或出生日期。",
  "required_fields": ["age", "birth_date"],
  "sort_order": 1,
  "is_active": true,
  "created_at": "2026-06-20T08:00:00Z",
  "updated_at": "2026-06-27T10:30:00Z"
}
```

---

### 15.3 Subject

```json
{
  "id": 1,
  "project_id": 1,
  "subject_no": "S-001",
  "site_name": "郑州中心",
  "gender": "男",
  "age": 32,
  "birth_year": 1994,
  "diagnosis": "晚期非小细胞肺癌",
  "material_count": 4,
  "screening_status": "need_review",
  "overall_result": "manual_review",
  "created_by": 1,
  "created_at": "2026-06-25T09:00:00Z",
  "updated_at": "2026-06-27T10:30:00Z"
}
```

---

### 15.4 UploadedFile

```json
{
  "id": 21,
  "project_id": 1,
  "subject_id": 1,
  "file_name": "住院病历_2026-06-12.pdf",
  "file_path": "oss://trialmatch/subjects/S-001/住院病历_2026-06-12.pdf",
  "file_type": "medical_record",
  "file_scope": "subject_data",
  "mime_type": "application/pdf",
  "file_size": 2048000,
  "page_count": 8,
  "parse_status": "parsed",
  "uploaded_by": 1,
  "uploaded_at": "2026-06-27T09:00:00Z"
}
```

---

### 15.5 CriterionEvaluation

```json
{
  "id": 9001,
  "run_id": 1001,
  "project_id": 1,
  "subject_id": 1,
  "criterion_id": 1,
  "criterion_code": "I-01",
  "criterion_type": "inclusion",
  "criterion_text": "年龄 18–75 周岁，男女不限。",
  "ai_result": "pass",
  "confidence_score": 96,
  "ai_rationale": "病例第 3 页显示患者出生日期为 1994-05-21，当前年龄 32 岁，满足 18–75 周岁的要求。",
  "manual_result": null,
  "manual_comment": null,
  "reviewer_id": null,
  "reviewed_at": null,
  "created_at": "2026-06-27T10:03:00Z",
  "updated_at": "2026-06-27T10:03:00Z"
}
```

---

### 15.6 EvaluationCitation

```json
{
  "id": 7001,
  "evaluation_id": 9001,
  "file_id": 21,
  "file_name": "住院病历_2026-06-12.pdf",
  "file_type": "medical_record",
  "page_no": 3,
  "chunk_id": 301,
  "quoted_text": "患者出生日期：1994-05-21，现年 32 岁。",
  "extracted_fact": "患者 1994-05-21 出生，现年 32 岁。",
  "relevance_explanation": "该证据支持患者年龄满足 18–75 周岁的入选标准。",
  "created_at": "2026-06-27T10:03:00Z"
}
```

---

## 16. MVP 接口优先级建议

### P0：必须实现

* `POST /auth/login`
* `GET /auth/me`
* `GET /projects`
* `POST /projects`
* `GET /projects/{project_id}`
* `PUT /projects/{project_id}`
* `GET /projects/{project_id}/criteria`
* `POST /projects/{project_id}/criteria`
* `PUT /criteria/{criterion_id}`
* `GET /projects/{project_id}/subjects`
* `POST /projects/{project_id}/subjects`
* `POST /subjects/{subject_id}/files`
* `GET /files`
* `POST /subjects/{subject_id}/screening-runs`
* `GET /subjects/{subject_id}/evaluations/latest`
* `GET /evaluations/{evaluation_id}`
* `PUT /evaluations/{evaluation_id}/manual-review`

### P1：建议尽快实现

* `POST /projects/{project_id}/files`
* `POST /files/{file_id}/parse`
* `GET /files/{file_id}/chunks`
* `GET /evaluations/{evaluation_id}/citations`
* `GET /citations/{citation_id}/context`
* `GET /projects/{project_id}/dashboard`
* `POST /subjects/{subject_id}/export-report`

### P2：后续增强

* `GET /audit-logs`
* `POST /projects/{project_id}/criteria/batch-import`
* `POST /screening-runs/{run_id}/rerun`
* `POST /subjects/{subject_id}/evaluations/batch-review`
* `GET /projects/{project_id}/screening-runs/stats`

