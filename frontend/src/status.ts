export function resultLabel(value?: string | null): string {
  switch (value) {
    case "recommended":
      return "建议入筛"
    case "excluded":
      return "疑似排除"
    case "manual_review":
      return "需人工确认"
    case "insufficient_data":
      return "资料不足"
    case "pass":
      return "证据支持"
    case "fail":
      return "未通过"
    case "exclusion_hit":
      return "命中排除"
    case "exclusion_not_hit":
      return "未命中排除"
    case "not_started":
      return "未开始"
    default:
      return value ?? "未开始"
  }
}

export function projectStatusLabel(value: string): string {
  switch (value) {
    case "screening":
      return "筛选中"
    case "configuring":
      return "配置中"
    case "paused":
      return "已暂停"
    case "draft":
      return "草稿"
    case "active":
      return "启用"
    default:
      return value
  }
}

export function badgeClass(value?: string | null): string {
  switch (value) {
    case "recommended":
    case "pass":
    case "exclusion_not_hit":
    case "completed":
    case "active":
    case "screening":
      return "tag tag-success"
    case "excluded":
    case "fail":
    case "exclusion_hit":
      return "tag tag-danger"
    case "manual_review":
    case "insufficient_data":
    case "need_review":
    case "configuring":
      return "tag tag-warning"
    case "running":
    case "parsing":
    case "parsed":
      return "tag tag-info"
    default:
      return "tag tag-muted"
  }
}
