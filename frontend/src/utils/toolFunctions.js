// 模拟天气API
export const mockWeatherAPI = async (location) => {
  console.log('[DEBUG] 调用模拟天气API，位置:', location);
  return `${location} 当前天气：24℃，晴`;
};

// 模拟查询人员档案信息
export const mockQueryPersonnelArchive = async (sql) => {
  console.log('[DEBUG] 调用查询人员档案API，SQL:', sql);
  
  // 这里可以添加SQL解析和验证逻辑
  if (!sql.toLowerCase().startsWith('select')) {
    throw new Error('仅支持SELECT查询');
  }

  // 返回模拟数据
  return [
    {
      name: '张三',
      age: 28,
      gender: '男',
      political_status: '党员',
      marital_status: '已婚'
    },
    {
      name: '李四',
      age: 32,
      gender: '女',
      political_status: '群众',
      marital_status: '未婚'
    }
  ];
};


