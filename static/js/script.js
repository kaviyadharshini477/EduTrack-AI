// ---------------------------------------
// Show Biology / Computer Science Field
// ---------------------------------------

const streamSelect = document.getElementById("stream");
const biologyDiv = document.getElementById("biologyDiv");
const csDiv = document.getElementById("csDiv");

streamSelect.addEventListener("change", function () {

    biologyDiv.style.display = "none";
    csDiv.style.display = "none";

    if (this.value === "Biology") {

        biologyDiv.style.display = "block";

    }

    else if (this.value === "Computer Science") {

        csDiv.style.display = "block";

    }

});

// ---------------------------------------
// Helper Function
// ---------------------------------------

function fillList(id, items) {

    const list = document.getElementById(id);

    list.innerHTML = "";

    if (!items || items.length === 0) {

        const li = document.createElement("li");
        li.innerText = "No information available.";
        list.appendChild(li);

        return;
    }

    items.forEach(item => {

        const li = document.createElement("li");

        li.innerText = item;

        list.appendChild(li);

    });

}

// ---------------------------------------
// Form Submit
// ---------------------------------------

document.getElementById("predictionForm").addEventListener("submit", async function (event) {

    event.preventDefault();

    const stream = document.getElementById("stream").value;

    let biology = 0;
    let computer_science = 0;

    if (stream === "Biology") {

        biology = parseFloat(document.getElementById("biology").value || 0);

    }

    if (stream === "Computer Science") {

        computer_science = parseFloat(document.getElementById("computer_science").value || 0);

    }

    const data = {

        stream: stream,

        study_hours: parseFloat(document.getElementById("study_hours").value),

        attendance: parseFloat(document.getElementById("attendance").value),

        sleep_hours: parseFloat(document.getElementById("sleep_hours").value),

        internet_usage: parseFloat(document.getElementById("internet_usage").value),

        mathematics: parseFloat(document.getElementById("mathematics").value),

        physics: parseFloat(document.getElementById("physics").value),

        chemistry: parseFloat(document.getElementById("chemistry").value),

        english: parseFloat(document.getElementById("english").value),

        biology: biology,

        computer_science: computer_science

    };

    try {

        // UPDATED API ROUTE
        const response = await fetch("/api/predict", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify(data)

        });

        const result = await response.json();

        console.log(result);

        document.getElementById("result").style.display = "block";

        // ---------------------------------------
        // Scores
        // ---------------------------------------

        document.getElementById("score").innerHTML =
            `${result.predicted_exam_score} / 100`;

        document.getElementById("previous_score").innerHTML =
            result.previous_score;

        // ---------------------------------------
        // Prediction Explanation
        // ---------------------------------------

        document.getElementById("predictionReason").innerText =
            result.ai_guidance.prediction_reason ||
            "No explanation available.";

        // ---------------------------------------
        // Performance
        // ---------------------------------------

        document.getElementById("performance").innerText =
            result.ai_guidance.performance_level;

        // ---------------------------------------
        // Motivation
        // ---------------------------------------

        document.getElementById("motivation").innerText =
            result.ai_guidance.motivation;

        // ---------------------------------------
        // Lists
        // ---------------------------------------

        fillList("strengths", result.ai_guidance.strengths);

        fillList("weaknesses", result.ai_guidance.weaknesses);

        fillList("studyplan", result.ai_guidance.study_plan);

        // ---------------------------------------
        // Career Cards
        // ---------------------------------------

        const careerDiv = document.getElementById("career");

        careerDiv.innerHTML = "";

        if (
            result.ai_guidance.career_suggestions &&
            result.ai_guidance.career_suggestions.length > 0
        ) {

            result.ai_guidance.career_suggestions.forEach(career => {

                const card = document.createElement("div");

                card.className = "career-card";

                card.innerHTML = `

                    <h4>${career.career}</h4>

                    <p>${career.reason}</p>

                `;

                careerDiv.appendChild(card);

            });

        }

        else {

            careerDiv.innerHTML =
                "<p>No career suggestions available.</p>";

        }

        window.scrollTo({

            top: document.body.scrollHeight,

            behavior: "smooth"

        });

    }

    catch (error) {

        console.error(error);

        alert("Something went wrong while generating the prediction.");

    }

});