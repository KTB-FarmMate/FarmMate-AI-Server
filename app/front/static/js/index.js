window.addEventListener("load", () => {
    const crops = Array.from(document.getElementsByClassName("crop"));

    const memberId = get_memberId();
    console.log(`${BE_SERVER}/members/${memberId}/threads`);
    const crops_data = JSON.parse(localStorage.getItem("crops_data"));

    let attempts = 0; // 시도 횟수
    const maxAttempts = 5; // 최대 재시도 횟수

    (function retryFetch() {
        fetch(`${BE_SERVER}/members/${memberId}/threads`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(cropDatas => {
                console.log("Fetched crop data:", cropDatas);

                let dataFound = false; // 데이터가 존재하는지 확인

                crops.forEach(crop => {
                    const cropName = crop.dataset.type; // crop 요소의 'data-type' 속성 값 가져오기

                    console.log("Checking crop:", cropDatas, cropName);

                    if (cropDatas[cropName]) {
                        dataFound = true;
                        crop.dataset.created = "true"; // 'data-created' 값을 true로 설정

                        crop.addEventListener("click", () => {
                            window.location.href = `/front/members/${memberId}/crop/${cropName}`;
                            localStorage.setItem("select_crop", cropName);
                        });
                    } else {
                        crop.addEventListener("click", () => {
                            window.location.href = `/front/members/${memberId}/crop_create/${cropName}`;
                        });
                    }
                });

                // 데이터가 발견되면 재시도 중단
                if (dataFound) {
                    console.log("Data found, stopping retries.");
                    return;
                }

                // 데이터가 없고 시도 횟수가 남아 있으면 재시도
                if (attempts < maxAttempts - 1) {
                    attempts++;
                    console.warn(`Attempt ${attempts}/${maxAttempts} failed. Retrying...`);
                    setTimeout(retryFetch, 100); // 1초 후 재시도
                } else {
                    console.error("Max retries reached. Data not found.");
                }
            })
            .catch(error => {
                console.error("Error fetching crop data:", error);

                // 에러 발생 시 재시도
                if (attempts < maxAttempts - 1) {
                    attempts++;
                    console.warn(`Attempt ${attempts}/${maxAttempts} failed. Retrying...`);
                    setTimeout(retryFetch, 100); // 1초 후 재시도
                } else {
                    console.error("Max retries reached. Fetch failed.");
                }
            });
    })();

});
