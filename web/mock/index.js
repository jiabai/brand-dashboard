export default [
  {
    url: '/api/task/current',
    method: 'GET',
    response: () => {
      return {
        success: true,
        taskName: '测试任务-' + Math.random().toString(36).substring(7)
      }
    }
  },
  {
    url: '/api/task/current',
    method: 'POST',
    response: ({ body }) => {
      return {
        success: true,
        message: '任务名称已更新',
        taskName: body.taskName
      }
    }
  }
]
