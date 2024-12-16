document.addEventListener("DOMContentLoaded", () => {


})


function get_weather(memberId, cropName) {
    // 현재 날씨 정보 요청
    const crop_data = JSON.parse(localStorage.getItem("crops_data"))[cropName];
    const temperature = document.querySelector(".temperature");
    const humidity = document.querySelector(".humidity");

    fetch(`${BE_SERVER}/weather/current?address=${crop_data.address}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
        }).then(data => {
        temperature.textContent = data.temperature;
        humidity.textContent = data.humidity;
        console.log(data);
    })
}

// 병해충 알림 요청
function get_pests(cropName) {
    // 현재 날씨 정보 요청
    fetch(`${BE_SERVER}/pests?cropName=${cropName}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
        })
        .then(data => {
            const warnings = document.querySelector(".alert-warnings");
            warnings.innerHTML = '';
            data["warnings"].forEach(element => {
                const span = document.createElement("span");
                span.textContent = element;
                warnings.appendChild(span);
            })
            const advisories = document.querySelector(".alert-advisories");
            advisories.innerHTML = '';
            data["advisories"].forEach(element => {
                const span = document.createElement("span");
                span.textContent = element;
                advisories.appendChild(span);
            })
            const foreCasts = document.querySelector(".alert-foreCasts");
            foreCasts.innerHTML = '';
            data["foreCasts"].forEach(element => {
                const span = document.createElement("span");
                span.textContent = element;
                foreCasts.appendChild(span);
            })
            console.log(data);
        })
}

// 재배 길라잡이 요청
function get_guidance(memberId, cropName) {
    const crops_data = JSON.parse(localStorage.getItem("crops_data"));
    const select_crop = crops_data[cropName];
    fetch(`${BE_SERVER}/members/${memberId}/threads/${select_crop.threadId}/status?cropId=${select_crop.cropId}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
        })
        .then(data => {
            console.log(data);
            const card_ul = document.querySelector(".card_content ul");
            data["recommendedActions"].forEach((action) => {
                const li = document.createElement("li");
                li.textContent = action
                card_ul.appendChild(li);
            })
        })
}
