function get_pest_detail(cropName, pestName) {
    // 작물명 한/중/영
    const name_kor = document.querySelector(".fest_name.kor");
    const name_chn = document.querySelector(".fest_name.chn");
    const name_eng = document.querySelector(".fest_name.eng");
    const crop_name = document.querySelector(".crop_name");

    // 질병 이미지 정보
    const fest_img_list = document.querySelector(".fests_img_container .img_list");
    // 질병 표지 정보
    const fest_preview_img = document.querySelector(".fest_img img");


    // 발생 환경
    const occurrence_env_content = document.querySelector(".occurrence_env_container .content");

    // 증상 설명
    const description_content = document.querySelector(".occurrence_env_container .content");

    // 예방 방법
    const control_content = document.querySelector(".control_container .content");
    fetch(`${BE_SERVER}/pests/${pestName}?cropName=${cropName}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error(response.statusText);
        })
        .then(data => {
            name_kor.innerHTML = `한글명: ${data?.sickNameKor || ""}`;
            name_chn.innerHTML = `한문명: ${data?.sickNameChn || ""}`;
            name_eng.innerHTML = `영문명: ${data?.sickNameEng || ""}`;
            crop_name.innerHTML = `작물명: ${data?.cropName || ""}`;

            // 발생 환경
            occurrence_env_content.innerHTML = data?.["developmentCondition"] ?? "";

            // 증상
            description_content.innerHTML = data?.["symptoms"] ?? "";

            // 예방법
            control_content.innerHTML = data?.["preventionMethod"] ?? "";

            // 이미지 리스트
            const image_list = data?.["imageList"] ?? [];

            let preview_img = "";
            if (image_list.length >= 1){
                fest_img_list.innerHTML = "";
            }
            image_list.forEach(image => {
                if (preview_img === "" && image.iemSpchcknNm === "병증상") {
                    preview_img = image.image;
                    fest_preview_img.src = preview_img;
                }
                const figure_element = document.createElement("figure");
                const image_element = document.createElement("img");
                const figcaption_element = document.createElement("figcaption");
                image_element.src = image.image;
                image_element.alt = image.imageTitle ?? "";
                figcaption_element.innerHTML = image.imageTitle ?? "";
                figure_element.appendChild(image_element);
                fest_img_list.appendChild(figure_element);
            })
        })
}

document.addEventListener("DOMContentLoaded", () => {

})