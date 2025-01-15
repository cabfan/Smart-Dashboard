// 模拟天气API
export const mockWeatherAPI = async (location) => {
  try {
    // 1. 先查询城市ID
    const lookupUrl = `https://geoapi.qweather.com/v2/city/lookup?location=${encodeURIComponent(location)}&range=cn&key=46c9ded06bd84ce5b833058495a1fd17`;
    const lookupResponse = await fetch(lookupUrl);
    const lookupData = await lookupResponse.json();

    // 检查是否找到城市
    if (lookupData.code !== '200' || !lookupData.location?.length) {
      return `无法找到 ${location} 的天气信息`;
    }

    // 取第一个匹配的城市
    const cityId = lookupData.location[0].id;
    const cityName = lookupData.location[0].name;

    // 2. 查询天气
    const weatherUrl = `https://devapi.qweather.com/v7/weather/now?location=${cityId}&key=46c9ded06bd84ce5b833058495a1fd17`;
    const weatherResponse = await fetch(weatherUrl);
    const weatherData = await weatherResponse.json();

    // 检查天气数据
    if (weatherData.code !== '200') {
      return `获取 ${cityName} 天气信息失败`;
    }
    return weatherData.now;

  } catch (error) {
    console.error('[ERROR] 获取天气信息失败:', error);
    return `获取 ${location} 天气信息失败，请稍后再试`;
  }
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

// 添加新的工具函数
export const getCurrentTime = async () => {
  try {
    // 调用自己的后端接口
    const response = await fetch('http://localhost:3001/api/current-time');
    const data = await response.json();

    if (!data.success) {
      throw new Error('获取时间失败');
    }

    // 将时间戳转换为北京时间
    const date = new Date(data.timestamp);
    const options = {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    };
    
    // 格式化日期时间
    const beijingTime = new Intl.DateTimeFormat('zh-CN', options).format(date);
    return `当前北京时间：${beijingTime}`;

  } catch (error) {
    console.error('[ERROR] 获取当前时间失败:', error);
    return '获取当前时间失败，请稍后再试';
  }
};

