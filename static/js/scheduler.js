itemFormContainer = document.getElementById("item-forms");
itemForms = itemFormContainer.getElementsByClassName("item-form");
editFormOpen = false;
currentScheduleId = null;
currentActivityId = null;
fixedBlockCount = 0;

function plural_to_single(item) {
    words = {
        activities: "activity",
    };

    if (!words[item]) {
        return item.slice(0, -1);
    }
    return words[item];
}

/**
 * Stop the default behaviour of forms of reloading the page
 */
sform = document.getElementById("schedules-form");
sform.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(sform);
    var object = {};
    formData.forEach((value, key) => {
        object[key] = value;
    });
    fetch(`/api/schedules/create`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(object),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then((data) => {
            console.log("Success:", data);
            sform.reset();
            generateScheduleTable();
            toggleForms();
        })
        .catch((error) => {
            console.error("Error:", error);
            document.getElementById("form-error-messages").textContent =
                "Schedule creation failed. Please try again.";
            document
                .getElementById("form-error-messages")
                .classList.remove("hidden");
        });
});

aform = document.getElementById("activities-form");
aform.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(aform);
    var object = {};
    var fixedBlocks = [];
    formData.forEach((value, key) => {
        if (key == "even_frequency_spacing") {
            object[key] = document.getElementById(key).checked;
        } else {
            object[key] = value;
        }
    });
    console.log(object);
    for (let fbIdx = 0; fbIdx < fixedBlockCount; fbIdx++) {
        fixedBlocks.append([
            object[`fixed-block-day-${fbIdx}`].object[
                `fixed-block-start-${fbIdx}`
            ].object[`fixed-block-end-${fbIdx}`],
        ]);
    }
    console.log(fixedBlocks);
    object["fixed"] = fixedBlocks;

    fetch(`/api/schedules/${currentScheduleId}/activities/create`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(object),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then((data) => {
            console.log("Success:", data);
            fixedBlockCount = 0;
            aform.reset();
            generateActivityTable(currentScheduleId);
            toggleForms();
        })
        .catch((error) => {
            console.error("Error:", error);
            document.getElementById("form-error-messages").textContent =
                "Activity creation failed. Please try again.";
            document
                .getElementById("form-error-messages")
                .classList.remove("hidden");
        });
});

function setActiveSchedule(id) {
    const prevSchedule = document.getElementById(
        `schedule-${currentScheduleId}`,
    );
    if (prevSchedule) {
        prevSchedule.classList.remove("selected");
    }

    enableTables();
    currentScheduleId = id;
    generateBlockTable(id);
    generateActivityTable(id);

    document.getElementById(`schedule-${id}`).classList.add("selected");

    if (document.getElementById('block-table-body').childElementCount != 0) {
        document.getElementById('generate-timetable-btn').disabled = true
        document.getElementById('anneal-timetable-btn').disabled = true
    }

}

function setActiveActivity(id) {
    const prevActivity = document.getElementById(
        `activity-${currentActivityId}`,
    );
    if (prevActivity) {
        prevActivity.classList.remove("selected");
    }

    if (id == currentActivityId) {
        generateBlockTable(currentScheduleId, null);
        currentActivityId = null;
        return;
    }

    currentActivityId = id;
    generateBlockTable(currentScheduleId, id);
    document.getElementById(`activity-${id}`).classList.add("selected");
}

/**
 * Toggle the item form containers.
 * If editMode is set to true, the 'Create' button is changed to 'Update'
 * @param {Boolean} editMode
 */
function toggleForms(item = "activities") {
    document.getElementById("backdrop").classList.toggle("hidden");
    document.getElementById("item-forms").classList.toggle("hidden");
    for (const container of document.getElementById("item-forms").children) {
        if (container.id != `${item}-form-container`) {
            container.classList.add("hidden");
        } else {
            container.classList.remove("hidden");
        }
    }
    document.getElementById("form-error-messages").textContent = "";
    document.getElementById("form-error-messages").classList.add("hidden");
}

async function fetchBlocks(sid, aid = null) {
    var url = `/api/schedules/${sid}/blocks`;
    if (aid) {
        url += `/activities/${aid}/blocks`;
    }
    const response = await fetch(url, {
        method: "GET",
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
    }
    blocks = await response.json();
    return blocks;
}

/**
 * Generates and populates the schedule table
 */
async function generateScheduleTable() {
    var url = `/api/schedules`;
    const response = await fetch(url, {
        method: "GET",
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
    }
    res = await response.json();

    const scheduleTable = document.getElementById("schedule-table-body");
    scheduleTable.innerHTML = "";
    let scheduleCount = 0;

    for (const schedule of res.schedules) {
        const row = document.createElement("tr");

        row.id = `schedule-${schedule.id}`;
        const nameText = document.createElement("td");
        nameText.textContent = schedule.name;
        const groupText = document.createElement("td");
        groupText.textContent = schedule.group_name;

        const startDateText = document.createElement("td");
        const startDate = new Date(schedule.start_date);
        startDateText.textContent = startDate.toLocaleDateString();

        const sizeText = document.createElement("td");
        sizeText.textContent = schedule.length;

        const slotSizeText = document.createElement("td");
        slotSizeText.textContent = schedule.slot_size;

        row.ondblclick = () => {
            setActiveSchedule(schedule.id);
        };
        row.append(nameText, groupText, startDateText, sizeText, slotSizeText);
        scheduleTable.append(row);
        scheduleCount += 1;
    }
    document.getElementById("schedule-counter").textContent = scheduleCount;
}

/**
 * Generates and populates the activity table
 */
async function generateActivityTable(id) {
    var url = `/api/schedules/${id}/activities`;
    const response = await fetch(url, {
        method: "GET",
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
    }
    res = await response.json();

    const activityTable = document.getElementById("activity-table-body");
    activityTable.innerHTML = "";
    let activityCount = 0;

    for (const activity of res.activities) {
        const row = document.createElement("tr");
        row.id = `activity-${activity.id}`;
        const activityTitleText = document.createElement("td");
        const activityColour = document.createElement("span");
        activityColour.classList.add("fa-solid", "fa-circle");
        activityColour.style.color = activity.colour;
        activityColour.style.marginRight = "5px";
        activityTitleText.append(activityColour);
        activityTitleText.innerHTML += activity.title;

        const priorityText = document.createElement("td");
        priorityText.textContent = activity.priority;

        const frequencyText = document.createElement("td");
        frequencyText.textContent = activity.frequency;

        const minTimeText = document.createElement("td");
        minTimeText.textContent = activity.min_time;
        const maxLengthText = document.createElement("td");
        maxLengthText.textContent = activity.max_length;

        row.ondblclick = () => {
            setActiveActivity(activity.id);
        };
        row.append(
            activityTitleText,
            priorityText,
            frequencyText,
            minTimeText,
            maxLengthText,
        );
        activityTable.append(row);
        activityCount += 1;
    }

    document.getElementById("activity-counter").textContent = activityCount;
}

/**
 * Generates and populates the blocks table
 */
async function generateBlockTable(sid, aid = null) {
    var url = `/api/schedules/${sid}`;
    if (aid) {
        url += `/activities/${aid}`;
    }
    url += `/blocks`;
    const response = await fetch(url, {
        method: "GET",
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
    }
    res = await response.json();

    const blockTable = document.getElementById("block-table-body");
    blockTable.innerHTML = "";
    let blockCount = 0;
    for (const block of res.blocks) {
        const row = document.createElement("tr");
        row.id = `block-${block.id}`;
        const blockTitleText = document.createElement("td");
        const blockColour = document.createElement("span");
        blockColour.classList.add("fa-solid", "fa-circle");
        blockColour.style.color = block.colour;
        blockColour.style.marginRight = "5px";
        blockTitleText.append(blockColour);
        blockTitleText.innerHTML += block.title;

        const blockStart = document.createElement("td");
        const startDateTime = new Date(block.start_datetime);
        const sDate = document.createElement("p");
        sDate.textContent = startDateTime.toLocaleDateString();
        const sTime = document.createElement("p");
        sTime.textContent = startDateTime
            .toLocaleTimeString()
            .replace(":00 ", " ");
        blockStart.append(sDate, sTime);

        const blockEnd = document.createElement("td");
        const endDateTime = new Date(block.end_datetime);
        const eDate = document.createElement("p");
        eDate.textContent = endDateTime.toLocaleDateString();
        const eTime = document.createElement("p");
        eTime.textContent = endDateTime
            .toLocaleTimeString()
            .replace(":00 ", " ");
        blockEnd.append(eDate, eTime);

        const blockStatus = document.createElement("td");
        blockStatus.textContent = "Uncompleted";

        row.append(blockTitleText, blockStart, blockEnd, blockStatus);
        blockTable.append(row);
        blockCount += 1;
    }

    document.getElementById("block-counter").textContent = blockCount;
    if (document.getElementById('block-table-body').childElementCount != 0) {
        document.getElementById('generate-timetable-btn').disabled = true
        document.getElementById('anneal-timetable-btn').disabled = true
    } else {
        document.getElementById('generate-timetable-btn').disabled = false
        document.getElementById('anneal-timetable-btn').disabled = false
    }
}

function addNewFixedBlock() {
    const fbt = document.getElementById("fixed-blocks-table");
    const row = document.createElement("tr");

    const day = document.createElement("td");
    const dayInput = document.createElement("input");
    dayInput.classList.add("field-input");
    dayInput.type = "number";
    dayInput.placeholder = `0-length`;
    dayInput.required = true;
    dayInput.name = `fixed-block-day-${fixedBlockCount}`;
    day.append(dayInput);

    const start = document.createElement("td");
    const startInput = document.createElement("input");
    startInput.classList.add("field-input");
    startInput.type = "time";
    startInput.required = true;
    startInput.name = `fixed-block-start-${fixedBlockCount}`;
    start.append(startInput);

    const end = document.createElement("td");
    const endInput = document.createElement("input");
    endInput.classList.add("field-input");
    endInput.type = "time";
    endInput.required = true;
    endInput.name = `fixed-block-end-${fixedBlockCount}`;
    end.append(endInput);

    row.append(day, start, end);
    fbt.append(row);
    fixedBlockCount++;
}

async function setupScheduler() {
    let settings = await fetchSettings();

    generateScheduleTable();
    disableTables();
}

function enableTables() {
    document.getElementById("activity-container").classList.remove("disabled");
    document.getElementById("block-container").classList.remove("disabled");
}

function disableTables() {
    document.getElementById("activity-container").classList.add("disabled");
    document.getElementById("block-container").classList.add("disabled");
}
async function deleteScheduleBlocks() {
    var url = `/api/schedules/${currentScheduleId}/blocks`;
    const response = await fetch(url, {
        method: "DELETE",
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
    }

    await generateBlockTable(currentScheduleId);
}

/**
 * Uses bubble-sort to sort the table by the selected column
 * @param {Number} column
 */
function sortTable(column, item = "block") {
    const table = document.getElementById(`${item}-table`);
    var switching = true;
    var shouldSwitch = false;
    var switchCount = 0;
    var sortDirection = "asc";
    while (switching) {
        switching = false;
        const rows = table.rows;
        for (var i = 1; i < rows.length - 1; i++) {
            shouldSwitch = false;
            current = rows[i].getElementsByTagName("td")[column];
            next = rows[i + 1].getElementsByTagName("td")[column];
            if (sortDirection == "asc") {
                if (
                    current.textContent.toLowerCase() >
                    next.textContent.toLowerCase()
                ) {
                    shouldSwitch = true;
                    break;
                }
            } else if (sortDirection == "desc") {
                if (
                    current.textContent.toLowerCase() <
                    next.textContent.toLowerCase()
                ) {
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchCount++;
        } else {
            if (switchCount == 0 && sortDirection == "asc") {
                sortDirection = "desc";
                switching = true;
            }
        }
    }
    const tableArrows = document.getElementsByClassName("table-sort-arrows");
    for (let index = 0; index < tableArrows.length; index++) {
        const element = tableArrows[index];
        element.classList.remove("fa-sort");
        element.classList.remove("fa-sort-asc");
        element.classList.remove("fa-sort-desc");
        if (index != column) {
            element.classList.add("fa-sort");
        }
        document
            .getElementsByClassName("table-sort-arrows")
            [column].classList.add(`fa-sort-${sortDirection}`);
    }
}

async function generateSchedule() {
    const atb = document.getElementById('anneal-timetable-btn');
    if (!atb) return;
    atb.disabled = true
    const gtb = document.getElementById('generate-timetable-btn');
    if (!gtb) return;
    gtb.disabled = true

    deleteScheduleBlocks();

    var url = `/api/engine/generate/${currentScheduleId}`;
    const response = await fetch(url, {
        method: "POST",
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
    }

    blocks = await response.json();

    generateBlockTable(currentScheduleId);

    return blocks;
}

async function annealSchedule() {

    const atb = document.getElementById('anneal-timetable-btn');
    if (!atb) return;
    atb.disabled = true
    const gtb = document.getElementById('generate-timetable-btn');
    if (!gtb) return;
    gtb.disabled = true


    deleteScheduleBlocks();
    const backdrop = document.getElementById("loading-backdrop");

    backdrop.classList.remove("hidden");
    var url = `/api/engine/anneal/${currentScheduleId}`;
    const response = await fetch(url, {
        method: "POST",
    });

    if (!response.ok) {
        backdrop.innerHTML +=
            "SOMETHING WENT WRONG, PLEASE CHECK CANOPY CONSOLE";
        throw new Error(`${response.status} ${response.statusText}`);
    } 

    blocks = await response.json();
    backdrop.classList.add("hidden");
    generateBlockTable(currentScheduleId);

    return blocks;
}

setupScheduler();
// close forms when Esc is pressed
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !itemFormContainer.classList.contains("hidden")) {
        toggleForms();
    }
});
