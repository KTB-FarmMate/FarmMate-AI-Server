// UI 업데이트 함수
function updateWeatherUI(data) {
    // 온도와 습도 업데이트
    const temperature = document.querySelector(".temperature");
    const humidity = document.querySelector(".humidity");
    const weather_img = document.querySelector(".weather_img");
    temperature.textContent = `${data.temperature}°`;
    humidity.textContent = `${data.humidity}%`;

    // skyConditionCode에 따라 이미지 변경
    let imgPath = "";
    switch (data.skyConditionCode) {
        case 1: // 맑음
            imgPath = "/front/static/img/sun.png";
            break;
        case 2: // 구름조금
            imgPath = "/front/static/img/partly_cloudy.png";
            break;
        case 3: // 구름많음
            imgPath = "/front/static/img/cloudy.png";
            break;
        case 4: // 흐림
            imgPath = "/front/static/img/overcast.png";
            break;
        default:
            imgPath = "/front/static/img/sun.png"; // 기본값
    }
    weather_img.src = imgPath; // 이미지 업데이트
    weather_img.alt = "현재 날씨 상태"; // 대체 텍스트 추가

    console.log("Weather data used:", data);
}

function get_current_weather(cropName) {
    // 현재 날씨 정보 요청
    const crop_data = JSON.parse(localStorage.getItem("crops_data"))[cropName];

    // 기본 데이터
    const default_data = {
        "precipitationTypeCode": 0,
        "humidity": 50,
        "skyConditionCode": 2,
        "temperature": 20,
        "precipitation": 0
    };

    fetch(`${BE_SERVER}/weather/current?address=${crop_data.address}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error(`HTTP Error: ${response.status}`);
            }
        })
        .then(data => updateWeatherUI(data))
        .catch(error => {
            console.error("Failed to fetch current weather, using default data:", error);
            updateWeatherUI(default_data); // 실패 시 기본 데이터 사용
        });

}

// 하늘 상태를 결정하는 함수 (오전/오후 요약용)
function determineSkyCondition(hours) {
    const conditionCount = {1: 0, 2: 0, 3: 0, 4: 0};
    hours.forEach(hour => {
        conditionCount[hour.skyConditionCode] += 1;
    });

    // 가장 많이 등장한 skyConditionCode 결정
    const maxCondition = Object.keys(conditionCount).reduce((a, b) =>
        conditionCount[a] >= conditionCount[b] ? a : b
    );

    // skyConditionCode에 따라 이미지 파일명 반환
    return getSkyImage(parseInt(maxCondition));
}

// skyConditionCode에 따라 이미지 경로 반환
function getSkyImage(code) {
    switch (code) {
        case 1:
            return "sun";         // 맑음
        case 2:
            return "partly_cloudy"; // 구름조금
        case 3:
            return "cloudy";      // 구름많음
        case 4:
            return "overcast";    // 흐림
        default:
            return "sun";    // 기타
    }
}

function get_short_weather(cropName) {
    const crop_data = JSON.parse(localStorage.getItem("crops_data"))[cropName];
    const container = document.getElementById("forecast-container");
    fetch(`${BE_SERVER}/weather/short-term?address=${crop_data.address}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error(`HTTP Error: ${response.status}`);
            }
        })
        .then(data => {
            // 데이터 동적 생성
            data.forEach((day, index) => {
                // 오전/오후 요약 이미지 결정
                const morning = day.hourForecastInfos.filter(hour => parseInt(hour.forecastTime) < 12); // 오전 데이터
                const afternoon = day.hourForecastInfos.filter(hour => parseInt(hour.forecastTime) >= 12); // 오후 데이터

                const morningSky = determineSkyCondition(morning);
                const afternoonSky = determineSkyCondition(afternoon);

                // 상단 요약 바 생성
                const dayCard = document.createElement("div");
                dayCard.className = "card week_weather_item flex flex-column";

                dayCard.innerHTML = `
        <div class="date_section flex flex-row flex-space-between align-center toggle_header" data-index="${index}">
            <div class="dates flex flex-column">
                <div>${index + 1}일 후</div>
                <div>${day.forecastDate}</div>
            </div>
            <div class="weather_summary flex flex-row align-center">
                <div class="morning_img flex flex-column">
                    <div>오전</div>
                    <img src="/front/static/img/${morningSky}.png" alt="오전 날씨">
                </div>
                <div class="afternoon_img flex flex-column">
                    <div>오후</div>
                    <img src="/front/static/img/${afternoonSky}.png" alt="오후 날씨">
                </div>
            </div>
            <div class="temp_summary">
                최고: ${day.maxTemperature === -999 ? "미정" : `${day.maxTemperature}°`} / 
                최저: ${day.minTemperature === -999 ? "미정" : `${day.minTemperature}°`}
            </div>
        </div>
        <div class="hourly_weather_container" id="day-${index}" style="display: none;">
            <div class="card weather_header flex flex-row flex-space-between">
                ${day.hourForecastInfos.map(hour => `
                    <div class="today_weather_item">
                        <div class="temp">${hour.temperature}°</div>
                        <div class="weather_img">
                            <img src="/front/static/img/${getSkyImage(hour.skyConditionCode)}.png" alt="">
                        </div>
                        <div class="time_stamp">${hour.forecastTime}</div>
                        <div class="humidity">습도: ${hour.humidity}%</div>
                    </div>
                `).join("")}
            </div>
        </div>
    `;

                container.appendChild(dayCard);
            });

            // 토글 이벤트
            document.querySelectorAll(".toggle_header").forEach(header => {
                header.addEventListener("click", () => {
                    const index = header.dataset.index;
                    const target = document.getElementById(`day-${index}`);

                    if (target.style.display === "none" || target.style.display === "") {
                        target.style.display = "block";
                    } else {
                        target.style.display = "none";
                    }
                });
            });
        })
        .catch(error => {
            console.error("Failed to fetch current weather, using default data:", error);
            // updateWeatherUI(default_data); // 실패 시 기본 데이터 사용
            [
                {
                    "forecastDate": "2024-12-18",
                    "maxTemperature": 0,
                    "minTemperature": -6,
                    "hourForecastInfos": [
                        {
                            "forecastTime": "00:00",
                            "precipitationProbability": 30,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 4,
                            "temperature": -3
                        },
                        {
                            "forecastTime": "01:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -4
                        },
                        {
                            "forecastTime": "02:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -4
                        },
                        {
                            "forecastTime": "03:00",
                            "precipitationProbability": 30,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 70,
                            "snowAmount": 0,
                            "skyConditionCode": 4,
                            "temperature": -4
                        },
                        {
                            "forecastTime": "04:00",
                            "precipitationProbability": 30,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 70,
                            "snowAmount": 0,
                            "skyConditionCode": 4,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "05:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 70,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "06:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 70,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -6
                        },
                        {
                            "forecastTime": "07:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 70,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "08:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 70,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "09:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 65,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -4
                        },
                        {
                            "forecastTime": "10:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 55,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -3
                        },
                        {
                            "forecastTime": "11:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 50,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -2
                        },
                        {
                            "forecastTime": "12:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 50,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -1
                        },
                        {
                            "forecastTime": "13:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 45,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": 0
                        },
                        {
                            "forecastTime": "14:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 45,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": 0
                        },
                        {
                            "forecastTime": "15:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 45,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -1
                        },
                        {
                            "forecastTime": "16:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 50,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -1
                        },
                        {
                            "forecastTime": "17:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 55,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -3
                        },
                        {
                            "forecastTime": "18:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 60,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -4
                        },
                        {
                            "forecastTime": "19:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 65,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "20:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 60,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "21:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 60,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "22:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 55,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "23:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 55,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -5
                        }
                    ]
                },
                {
                    "forecastDate": "2024-12-19",
                    "maxTemperature": 4,
                    "minTemperature": -8,
                    "hourForecastInfos": [
                        {
                            "forecastTime": "00:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 55,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "01:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 60,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -6
                        },
                        {
                            "forecastTime": "02:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 60,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -6
                        },
                        {
                            "forecastTime": "03:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 65,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -6
                        },
                        {
                            "forecastTime": "04:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 65,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -6
                        },
                        {
                            "forecastTime": "05:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 65,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -7
                        },
                        {
                            "forecastTime": "06:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 70,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -7
                        },
                        {
                            "forecastTime": "07:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -7
                        },
                        {
                            "forecastTime": "08:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 80,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -7
                        },
                        {
                            "forecastTime": "09:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 60,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -5
                        },
                        {
                            "forecastTime": "10:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 50,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -3
                        },
                        {
                            "forecastTime": "11:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 45,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -1
                        },
                        {
                            "forecastTime": "12:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 40,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": 1
                        },
                        {
                            "forecastTime": "13:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 35,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": 2
                        },
                        {
                            "forecastTime": "14:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 35,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": 3
                        },
                        {
                            "forecastTime": "15:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 35,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": 3
                        },
                        {
                            "forecastTime": "16:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 40,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": 2
                        },
                        {
                            "forecastTime": "17:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 60,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": 1
                        },
                        {
                            "forecastTime": "18:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 65,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -1
                        },
                        {
                            "forecastTime": "19:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -2
                        },
                        {
                            "forecastTime": "20:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -3
                        },
                        {
                            "forecastTime": "21:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -4
                        },
                        {
                            "forecastTime": "22:00",
                            "precipitationProbability": 0,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 1,
                            "temperature": -3
                        },
                        {
                            "forecastTime": "23:00",
                            "precipitationProbability": 30,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 4,
                            "temperature": -3
                        }
                    ]
                },
                {
                    "forecastDate": "2024-12-20",
                    "maxTemperature": 5,
                    "minTemperature": -5,
                    "hourForecastInfos": [
                        {
                            "forecastTime": "00:00",
                            "precipitationProbability": 30,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 4,
                            "temperature": -3
                        },
                        {
                            "forecastTime": "03:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 75,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -4
                        },
                        {
                            "forecastTime": "06:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 70,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -4
                        },
                        {
                            "forecastTime": "09:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 65,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": -3
                        },
                        {
                            "forecastTime": "12:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 50,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": 3
                        },
                        {
                            "forecastTime": "15:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 55,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": 5
                        },
                        {
                            "forecastTime": "18:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 80,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": 2
                        },
                        {
                            "forecastTime": "21:00",
                            "precipitationProbability": 20,
                            "precipitationTypeCode": 0,
                            "precipitationAmount": 0,
                            "humidity": 90,
                            "snowAmount": 0,
                            "skyConditionCode": 3,
                            "temperature": 0
                        }
                    ]
                }
            ].forEach((day, index) => {
                // 오전/오후 요약 이미지 결정
                const morning = day.hourForecastInfos.filter(hour => parseInt(hour.forecastTime) < 12); // 오전 데이터
                const afternoon = day.hourForecastInfos.filter(hour => parseInt(hour.forecastTime) >= 12); // 오후 데이터

                const morningSky = determineSkyCondition(morning);
                const afternoonSky = determineSkyCondition(afternoon);

                // 상단 요약 바 생성
                const dayCard = document.createElement("div");
                dayCard.className = "card week_weather_item flex flex-column";

                dayCard.innerHTML = `
        <div class="date_section flex flex-row flex-space-between align-center toggle_header" data-index="${index}">
            <div class="dates flex flex-column">
                <div>${index + 1}일 후</div>
                <div>${day.forecastDate}</div>
            </div>
            <div class="weather_summary flex flex-row align-center">
                <div class="morning_img flex flex-column">
                    <div>오전</div>
                    <img src="/front/static/img/${morningSky}.png" alt="오전 날씨">
                </div>
                <div class="afternoon_img flex flex-column">
                    <div>오후</div>
                    <img src="/front/static/img/${afternoonSky}.png" alt="오후 날씨">
                </div>
            </div>
            <div class="temp_summary">
                최고: ${day.maxTemperature}° / 최저: ${day.minTemperature}°
            </div>
        </div>
        <div class="hourly_weather_container" id="day-${index}" style="display: none;">
            <div class="card weather_header flex flex-row flex-space-between">
                ${day.hourForecastInfos.map(hour => `
                    <div class="today_weather_item">
                        <div class="temp">${hour.temperature}°</div>
                        <div class="weather_img">
                            <img src="/front/static/img/${getSkyImage(hour.skyConditionCode)}.png" alt="">
                        </div>
                        <div class="time_stamp">${hour.forecastTime}</div>
                        <div class="humidity">습도: ${hour.humidity}%</div>
                    </div>
                `).join("")}
            </div>
        </div>
    `;

                container.appendChild(dayCard);
            });

            // 토글 이벤트
            document.querySelectorAll(".toggle_header").forEach(header => {
                header.addEventListener("click", () => {
                    const index = header.dataset.index;
                    const target = document.getElementById(`day-${index}`);

                    if (target.style.display === "none" || target.style.display === "") {
                        target.style.display = "block";
                    } else {
                        target.style.display = "none";
                    }
                });
            });
        });


}


document.addEventListener("DOMContentLoaded", () => {

})