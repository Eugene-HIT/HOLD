# 2026-06-15 HOLD 进度墙周分页时间轴与emoji头图

## 任务名称
HOLD 进度墙收紧时间轴跨度并简化顶部视觉

## 修改位置
- web/hold-progress-wall/src/components/records-timeline.tsx
- web/hold-progress-wall/src/components/emoji-hero.tsx
- web/hold-progress-wall/src/components/progress-wall-app.tsx
- web/hold-progress-wall/src/app/globals.css

## 本次完成内容
- 将原先按全部时间跨度拉伸的时间轴改为按周分页显示
- 新增上一周/下一周切换，默认自动定位到当前选中记录所在周
- 删除原像素人物头图组件，改为更轻的 emoji 头图
- 清理不再使用的像素角色样式，避免头部继续显得拥挤
- 后续继续将周视图局部改为横向滚动，避免局部仍显得过宽
- 将顶部 emoji 头图改为无边框的大面积漂浮动效，去掉额外说明文字和小卡片

## 关键实现说明
- 旧版时间轴按所有记录的最小开始时间和最大结束时间统一缩放，跨度一大就会拖长整个中部区域
- 新版把视图固定为单周窗口，只显示落在该周内的记录，并允许周切换
- 记录若跨周，会在当前周内按截断区间显示，保证版面稳定
- 顶部视觉改为纯 emoji 卡片，不再维护像素角色动画和额外装饰

## 验证结果
- npm run lint：通过
- npm run build：通过

## 追加收口
- 已将单周时间轴容器改为局部横向滚动，避免仍显得过宽
- 已将顶部 emoji 区调整为填充式漂浮动效，去掉卡片框和多余说明文字

## 待确认事项
- 当前按周分页是单周窗口，如果后续需要按月查看，可以在此基础上继续扩展成周/月切换
- emoji 当前采用简洁外星人和飞船风格，如需更偏工具感或更偏可爱感，可继续替换