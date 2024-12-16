document.addEventListener("DOMContentLoaded", () => {
    const crops = Array.from(document.getElementsByClassName("crop"));

    const memberId = localStorage.getItem("memberId");

    const crops_data = JSON.parse(localStorage.getItem("crops_data"));

    fetch(`${BE_SERVER}/members/${memberId}/threads`)
        .then(response => response.json())
        .then(cropDatas => {
            console.log(cropDatas);

            crops.forEach(crop => {
                const cropName = crop.dataset.type; // crop 요소의 'data-type' 속성 값을 가져옴

                // fetch로 가져온 데이터에 작물이 있는 경우
                console.log(cropDatas, cropName);
                if (cropDatas[cropName]) {
                    crop.dataset.created = "true"; // 'data-created' 값을 true로 설정
                    // crops_data[cropName].created = true;

                    crop.addEventListener("click", () => {
                        // 이미 생성된 작물 페이지로 이동
                        window.location.href = `crop/${cropName}`;
                        localStorage.setItem("select_crop", cropName);
                    });
                } else {
                    // fetch 데이터에 작물이 없는 경우
                    crop.addEventListener("click", () => {
                        // 새로운 작물 생성 페이지로 이동
                        window.location.href = `crop_create/${cropName}`;
                    });
                }
            });
        })
        .catch(error => {
            console.error("Error fetching crop data:", error);
        });
});
