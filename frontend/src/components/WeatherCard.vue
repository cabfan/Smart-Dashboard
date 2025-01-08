<template>
    <div class="weather-container">
      <div class="weather-header">
        <h2>天气信息</h2>
        <p>{{ formattedTime }}</p>
      </div>
  
      <div class="weather-main">
   
        <div class="weather-details">
          <h3>{{ weatherData.text }}</h3>
          <p><strong>温度：</strong>{{ weatherData.temp }}°C</p>
          <p><strong>体感温度：</strong>{{ weatherData.feelsLike }}°C</p>
          <p><strong>湿度：</strong>{{ weatherData.humidity }}%</p>
          <p><strong>气压：</strong>{{ weatherData.pressure }} hPa</p>
        </div>
      </div>
  
      <div class="weather-wind">
        <h4>风况</h4>
        <p><strong>风向：</strong>{{ weatherData.windDir }}</p>
        <p><strong>风速：</strong>{{ weatherData.windSpeed }} km/h</p>
        <p><strong>风力：</strong>{{ windScale }}</p>
      </div>
  
      <div class="weather-other">
        <h4>其他信息</h4>
        <p><strong>能见度：</strong>{{ weatherData.vis }} km</p>
        <p><strong>云量：</strong>{{ weatherData.cloud }}%</p>
        <p><strong>露点：</strong>{{ weatherData.dew }}°C</p>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'WeatherCard',
    props: {
      weatherData: {
        type: Object,
        required: true
      }
    },
    computed: {
      // 格式化时间
      formattedTime() {
        const date = new Date(this.weatherData.obsTime);
        return date.toLocaleString(); // 转换为本地时间
      },
      // 获取天气图标的 URL（假设图标是通过 icon 代码来显示的）
      weatherIconUrl() {
        return `https://cdn.weatherapi.com/weather/64x64/day/${this.weatherData.icon}.png`;
      },
      // 根据风力等级提供描述
      windScale() {
        const scale = parseInt(this.weatherData.windScale);
        if (scale <= 1) return "微风";
        if (scale <= 3) return "轻风";
        if (scale <= 5) return "中风";
        if (scale <= 7) return "强风";
        return "暴风";
      }
    }
  }
  </script>
  
  <style scoped>
  .weather-container {
    padding: 20px;
    background-color: #f9f9f9;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
  
  .weather-header {
    text-align: center;
    margin-bottom: 20px;
  }
  
  .weather-header h2 {
    font-size: 24px;
    font-weight: bold;
  }
  
  .weather-header p {
    font-size: 14px;
    color: #888;
  }
  
  .weather-main {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
 
  .weather-details {
    flex: 1;
    padding-left: 20px;
  }
  
  .weather-details h3 {
    font-size: 18px;
    margin-bottom: 10px;
  }
  
  .weather-details p {
    font-size: 16px;
    color: #555;
  }
  
  .weather-wind, .weather-other {
    margin-top: 20px;
  }
  
  .weather-wind h4, .weather-other h4 {
    font-size: 16px;
    margin-bottom: 10px;
  }
  
  .weather-wind p, .weather-other p {
    font-size: 14px;
    color: #666;
  }
  </style>
  