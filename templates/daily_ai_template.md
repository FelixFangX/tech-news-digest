# 技术快讯 | {{date}}

> 每天自动生成 | 更新周期: 每日 08:00 (UTC+8)
> 数据来源: OpenAlex · GitHub Trending · StackOverflow

---

## 📌 今日要点

{{ai_summary}}

---

{{#if trends}}
### 📊 趋势信号

{{#if trends.rising}}
**📈 上升趋势：** {{trends.rising}}
{{/if}}

{{#if trends.stable}}
**🔍 持续热门：** {{trends.stable}}
{{/if}}

{{#if trends.emerging}}
**⚡ 新兴焦点：** {{trends.emerging}}
{{/if}}

{{/if}}

---

## 🤖 AI 资讯

{{#each ai_news}}
### {{title}}
{{#if ai_judgment}}
> {{ai_judgment}}
{{/if}}
- **来源**: OpenAlex
- **论文**: [{{title}}]({{url}})
- **发表**: {{published}}
{{#if abstract}}
- **摘要**: {{abstract}}
{{/if}}

{{/each}}

---

## 🔥 GitHub Trending

{{#each github_trending}}
### {{rank}}. {{name}}
{{#if description}}> {{description}}{{/if}}
{{#if gh_judgment}}
> {{gh_judgment}}
{{/if}}

- **语言**: {{language}} | **⭐**: {{stars}} | **🔱**: {{forks}}
- **今日新增**: +{{today_stars}} ⭐
- **链接**: [GitHub]({{url}})

---

{{/each}}

---

## 💬 StackOverflow 技术热点

{{#each stackoverflow}}
### {{title}}
{{#if so_judgment}}
> {{so_judgment}}
{{/if}}
- **标签**: {{#each tags}}`{{this}}` {{/each}}
- **投票**: {{votes}} | **回答**: {{answers}} | **浏览**: {{views}}
- **链接**: [查看问题]({{link}})

{{/each}}

---

> 📬 订阅此仓库: Watch → Releases only | 如需定制化需求 Open Issue
