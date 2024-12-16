document.addEventListener("DOMContentLoaded", () => {
    // 현재 날씨 정보 요청
    let select_crop = localStorage.getItem("select_crop");
    if (!select_crop) {
        let select_crop = decodeURIComponent(window.location.pathname.split("/")[3]);
        localStorage.setItem("select_crop", select_crop);
    }
    let crop_data = JSON.parse(localStorage.getItem("crops_data"))[select_crop];
    let memberId = localStorage.getItem("memberId");
    let temperature = document.querySelector(".temperature");
    let humidity = document.querySelector(".humidity");

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
    // 병해충 알림 요청
    // 재배 길라잡이 요청
    fetch(`${BE_SERVER}/members/${memberId}/threads/${crop_data.threadId}/status`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
        })
        .then(data => {
            console.log(data);
            const card_ul = document.querySelector(".card_content ul");
            data["recommendedActions"].forEach((action) => {
                let li = document.createElement("li");
                li.textContent = action
                card_ul.appendChild(li);
            })
        })
})