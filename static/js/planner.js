displayDateElement = document.getElementById("displayDate");
displayDate = new Date();
if (displayDateElement) {
    displayDate = new Date(displayDateElement.dataset.date);
}

dayMapping = {};

selectedBlock = null;

blockDragging = false;
startHandleDragging = false;
dragOffsetX = 0;
dragOffsetY = 0;

editing = false;

/**
 *  Fetches all timetable items (unfiltered)
 *  @returns {JSON}
 */
async function fetchPayload() {
    const dates = document.getElementsByClassName("day-container");
    const dpv = window.settings["days_per_view"];
    const response = await fetch(
        // `/api/timetable/range/?start=${dates[0].dataset.isoDate}&end=${dates[dpv - 1].dataset.isoDate}`,
        `/api/timetable/range/?start=${dayMapping["0"]}&end=${dayMapping[`${dpv - 1}`]}`,
        {
            method: "GET",
        },
    );

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
    }
    return response.json();
}

/**
 * Generates the days and their respective containers
 */
function generateDays() {
    window.dayContainers = window.dayContainers || [];
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const legend = document.getElementById("tt-legend");
    const schedule = document.getElementById("tt-schedule");
    legend.innerHTML = '<div id="tt-time">-</div>';
    const msInDay = 24 * 60 * 60 * 1000;
    var now;
    if (displayDate) {
        now = new Date(displayDate);
    } else {
        now = new Date();
    }
    window.dayContainers.forEach((element) => {
        element.remove();
    });
    const dpv = window.settings["days_per_view"];
    for (let inc = 0; inc < dpv; inc++) {
        var dayIdx = (inc + window.settings["start_day"]) % 7;
        const day = days[dayIdx + 7 - dpv];
        if (dayIdx < window.settings["start_day"]) {
            dayIdx -= dpv;
        }
        const nextDay = new Date(
            now.getTime() + msInDay * (1 - now.getDay() + dayIdx),
        );
        const newDay = document.createElement("div");
        newDay.id = `day-${day}`;
        newDay.classList.add("tt-weekday");

        const dayName = document.createElement("span");
        dayName.textContent = `${day}`;
        dayName.className = "day-name";
        const dayDate = document.createElement("span");
        dayDate.textContent = nextDay.toDateString().slice(4);
        dayDate.className = "day-date";
        newDay.append(dayName, document.createElement("br"), dayDate);

        dayMapping[`${nextDay.toDateString().slice(4)}`] = inc;
        dayMapping[inc] = `${nextDay.toISOString().slice(0, 10)}`;

        // const newDayCont = document.createElement("div");
        // newDayCont.id = `day-container-${day}`;
        // newDayCont.classList.add("day-container");
        // newDayCont.dataset.date = nextDay.toDateString().slice(3);
        // newDayCont.dataset.isoDate = nextDay.toISOString().slice(0, 10);
        // schedule.appendChild(newDayCont);
        // window.dayContainers.push(newDayCont);
        legend.appendChild(newDay);
    }
}

/**
 * Generates the numbers on the top timeline
 */
function generateTimeline() {
    document.getElementById("tt-timeline").innerHTML = "";
    for (let inc = 0; inc < 24; inc++) {
        const hour = (inc + window.settings["start_hour"]) % 24;
        const timeline = document.getElementById("tt-timeline");
        const timelineNumber = document.createElement("div");

        if (hour >= 12) {
            timelineNumber.classList.add("timeline-number-pm");
        } else {
            timelineNumber.classList.add("timeline-number");
        }
        timelineNumber.innerText = hour;
        timeline.appendChild(timelineNumber);
    }
}

/**
 * Generates the grids that identify day and hour boundaries
 */
function buildGrid() {
    const hl = document.getElementById("hour-lines");
    const dl = document.getElementById("day-lines");

    let hlHtml = "";
    for (let i = 0; i < 24; i++) hlHtml += "<div></div>";
    hl.innerHTML = hlHtml;

    let dlHtml = "";
    for (let i = 0; i < 7; i++) dlHtml += "<div></div>";
    dl.innerHTML = dlHtml;
}

/**
 * Gives the current progress through the day as a value from (0.0 - 1.0)
 * @returns {number}
 */
function dayProgress() {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const msSinceMidnight = now - start;
    const dayMs = 24 * 60 * 60 * 1000;
    return msSinceMidnight / dayMs;
}

/**
 * Gives the progress through the schedule (starting from the set startHour instead of 0:00)
 * @returns {number}
 */
function scheduleProgress() {
    const now = new Date();
    const start = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
        window.settings["start_hour"],
        0,
        0,
        0,
    );
    const dayMs = 24 * 60 * 60 * 1000;
    let elapsed = now - start;
    if (elapsed < 0) elapsed += dayMs;

    return elapsed / dayMs;
}

/**
 * Moves the current time marker
 */
function alignTimeMarker() {
    if (window.settings.timetable_view == "horizontal") {
        const left =
            document.getElementById("tt-timeline").scrollWidth *
            scheduleProgress();
        document.getElementById("time-marker").style.left = left + "px";
    } else {
        const top =
            document.getElementById("tt-timeline").scrollHeight *
            scheduleProgress();
        document.getElementById("time-marker").style.top = top + "px";
    }
}

/**
 * Scroll the value so the timemarker is visible
 */
function alignTimetimetableView() {
    const schedule = document.getElementById("tt-schedule-container");
    const marker = document.getElementById("time-marker");
    if (window.settings.timetable_view == "horizontal") {
        var scroll = parseInt(marker.style.left) - schedule.scrollWidth / 24;
        if (scroll < 0) scroll = 0;
        schedule.scrollLeft = scroll;
    } else {
        var scroll = parseInt(marker.style.top) - schedule.scrollHeight / 24;
        if (scroll < 0) scroll = 0;
        schedule.scrollTop = scroll;
    }
}

/**
 * Update the clock on the top left corner of the timetable
 */
function updateTime() {
    const clock = document.getElementById("tt-time");
    const now = new Date();
    let hours = formatTime(now.getHours());
    let minutes = formatTime(now.getMinutes());

    clock.innerHTML = hours + ":" + minutes;
}

/**
 *
 * @param {HTMLDivElement} target
 * @returns
 */
function showPopupMenu(target, e) {
    const popupMenu = document.getElementById("popup-menu");

    const alreadyOpen =
        popupMenu.classList.contains("open") &&
        target === popupMenu._currentTarget;

    console.log(alreadyOpen);
    if (alreadyOpen) {
        closePopupMenu();
        return;
    }

    const elBound = target.getBoundingClientRect();

    if (
        elBound.top + elBound.height + popupMenu.clientHeight >=
        document.documentElement.clientHeight
    ) {
        popupMenu.style.bottom = "10px";
        popupMenu.style.top = "unset";
    } else {
        popupMenu.style.bottom = "unset";
        popupMenu.style.top = `${elBound.top + elBound.height}px`;
    }

    if (
        e.pageX + popupMenu.clientWidth >=
        document.documentElement.clientWidth
    ) {
        popupMenu.style.right = "10px";
        popupMenu.style.left = "unset";
    } else {
        popupMenu.style.right = "unset";
        popupMenu.style.left = `${e.pageX}px`;
    }

    popupMenu._currentTarget = target;
    popupMenu.classList.add("open");
}

function closePopupMenu() {
    const popupMenu = document.getElementById("popup-menu");
    if (!popupMenu) return;
    popupMenu.classList.remove("open");
    if (popupMenu._currentTarget) {
        delete popupMenu._currentTarget;
    }
}

/**
 * Places the block into holding
 * @param {HTMLDivElement} block
 */
function holdBlock(block = null) {
    const popupMenu = document.getElementById("popup-menu");
    const schedule = document.getElementById("tt-schedule");
    const holdingPen = document.getElementById("block-holding");
    if (!block) {
        block = popupMenu._currentTarget;
    }
    if (block in schedule.childNodes) schedule.removeChild(block);
    holdingPen.append(block);
    block.classList.remove("selected");
    block.classList.add("held-block");
    block.dataset.held = 1;

    const startHandle = document.getElementById("start-handle");
    const endHandle = document.getElementById("end-handle");

    startHandle.style.visibility = "hidden";
    endHandle.style.visibility = "hidden";

    closePopupMenu();
}

async function deleteBlock() {
    if (!confirm((message = "Are you sure you want to delete this block?")))
        return;

    const popupMenu = document.getElementById("popup-menu");
    const blockId = popupMenu._currentTarget.dataset.blockId;
    const response = await fetch(`/api/timetable/block/${blockId}`, {
        method: "DELETE",
    });
    document
        .getElementsByName(`timetable-block-${blockId}`)
        .forEach((block) => block.remove());
    closePopupMenu();
}

async function editBlock(target) {
    console.log("edit");
}

/**
 * Marks the selected block as completed
 *
 * @returns {JSON}
 */
async function completeBlock() {
    const popupMenu = document.getElementById("popup-menu");
    const response = await fetch(
        `/api/timetable/block/${popupMenu._currentTarget.dataset.blockId}`,
        {
            method: "PUT",
            body: JSON.stringify({ completed: true }),
        },
    );

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
    }
    return response.json();
}

function markRescheduleBlock() {
    console.log("mark resc");
}

function spawnShadowBlock() {
    const shadow = document.createElement("div");
    shadow.id = "shadow-block";
    shadow.style.visibility = "hidden";
    document.getElementById("tt-schedule").append(shadow);
}

function spawnBlockHandles() {
    const minsInDay = 24 * 60;
    const startHandle = document.createElement("div");
    const endHandle = document.createElement("div");
    startHandle.id = "start-handle";
    endHandle.id = "end-handle";
    startHandle.dataset.resize = "start";
    endHandle.dataset.resize = "end";
    startHandle.classList.add("block-handle");
    endHandle.classList.add("block-handle");
    startHandle.style.visibility = "hidden";
    endHandle.style.visibility = "hidden";
    startHandle.draggable = true;
    endHandle.draggable = true;
    document.getElementById("tt-schedule").append(startHandle, endHandle);

    const handleWidthPx = 15;

    const scheduleContainer = document.getElementById("tt-schedule-container");
    const schedule = document.getElementById("tt-schedule");

    let currentHandle = "";
    let startDims = {};
    let startX = 0;
    let startY = 0;
    let startW = 0;
    let startH = 0;
    let startL = 0;
    let startT = 0;
    let snapXpx = (1 / snapX) * schedule.scrollWidth;
    let snapYpx = (1 / snapY) * schedule.scrollHeight;
    let snappedPos = 0;
    let snappedLength = 0;
    let snapUnitpx = 0;

    const onPointerDown = (e) => {
        if (e.button !== undefined && e.button !== 0) return;

        const handle = e.target.closest(".block-handle");
        if (!handle) return;

        currentHandle = handle.dataset.resize;

        startX = e.clientX;
        startY = e.clientY;
        startW = parseFloat(selectedBlock.style.getPropertyValue("--width"));
        startH = parseFloat(selectedBlock.style.getPropertyValue("--height"));
        startL = parseFloat(selectedBlock.style.getPropertyValue("--left"));
        startT = parseFloat(selectedBlock.style.getPropertyValue("--top"));

        window.addEventListener("pointermove", onPointerMove);
        window.addEventListener("pointerup", onPointerUp);
        e.preventDefault();
    };

    const onPointerMove = (e) => {
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        let newW = startW;
        let newH = startH;
        let newL = startL;
        let newT = startT;

        if (window.settings.timetable_view == "horizontal") {
            if (currentHandle == "start") {
                newL = startL + dx;
                if (newL >= snapXpx) {
                    newW = Math.max(0, startW - dx + snapXpx);
                }
                newL = Math.max(0, Math.min(newL, schedule.scrollWidth - newW));
                let snapL = newL;
                let snappedL = snapL - (snapL % snapXpx);
                startHandle.style.setProperty(
                    "--left",
                    `${snappedL - handleWidthPx}px`,
                );
            }
            if (currentHandle == "end") {
                newW = Math.max(
                    0,
                    Math.min(startW + dx, schedule.scrollWidth - newL),
                );
                let snapL = newW + startL;
                let snappedL = snapL - (snapL % snapXpx);
                endHandle.style.setProperty("--left", `${snappedL}px`);
            }

            let snappedW = newW - (newW % snapXpx);
            let snappedL = newL - (newL % snapXpx);
            selectedBlock.style.setProperty("--width", `${snappedW}px`);
            selectedBlock.style.setProperty("--left", `${snappedL}px`);

            snappedLength = snappedW;
            snappedPos = snappedL;
            snapUnitpx = snapXpx;
        } else {
            if (currentHandle == "start") {
                newH = Math.max(0, startH - dx + snapYpx);
                newT = Math.max(0, startT + dx);
                let snapT = newT;
                let snappedT = snapT - (snapT % snapYpx);
                startHandle.style.setProperty(
                    "--top",
                    `${snappedT - handleWidthPx}px`,
                );
            }
            if (currentHandle == "end") {
                newH = Math.max(0, startH + dx);
                let snapT = newH + startT;
                let snappedT = snapT - (snapT % snapYpx);
                endHandle.style.setProperty("--top", `${snappedT}px`);
            }

            let snappedH = newH - (newH % snapXpx);
            let snappedT = newT - (newT % snapXpx);
            selectedBlock.style.setProperty("--height", `${snappedH}px`);
            selectedBlock.style.setProperty("--top", `${snappedT}px`);

            snappedLength = snappedH;
            snappedPos = snappedT;
            snapUnitpx = snapYpx;
        }

        const startFullMins = Math.ceil(snappedPos / snapUnitpx) * 10;
        const endFullMins =
            Math.ceil((snappedPos + snappedLength) / snapUnitpx) * 10; // slot size

        const startHour = Math.floor(startFullMins / 60);
        const startMin = startFullMins % 60;
        const endHour = Math.floor(endFullMins / 60);
        const endMin = endFullMins % 60;

        const lengthFullMins = endFullMins - startFullMins;

        var sTime = `${formatTime(startHour)}:${formatTime(startMin)} `;
        var eTime = ` ${formatTime(endHour)}:${formatTime(endMin)}`;
        var displayTime = `${sTime}-${eTime}`;

        const timeSpan = selectedBlock
            .getElementsByClassName("block-time")
            .item(0);

        selectedBlock.dataset.blockLength = lengthFullMins;
        selectedBlock.dataset.blockTime = displayTime;
        selectedBlock.dataset.edited = true;
        timeSpan.textContent = displayTime;
    };

    const onPointerUp = (e) => {
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
        currentHandle = "";
    };

    startHandle.addEventListener("pointerdown", onPointerDown);
    endHandle.addEventListener("pointerdown", onPointerDown);
}

/**
 * Creates a block and splits it if it goes over visible time.
 * Returns an array of HTMLDivElements
 *
 * @param {Object} block
 * @returns {Array[HTMLDivElement]}
 */
function splitBlock(block) {
    const startHandle = document.getElementById("start-handle");
    const endHandle = document.getElementById("end-handle");
    const schedule = document.getElementById("tt-schedule");
    const pieces = [];
    const minsInDay = 24 * 60;
    const dpv = window.settings["days_per_view"];
    const shadow = document.getElementById("shadow-block");
    const timelineHeight = document.getElementById("tt-timeline").scrollHeight;
    const timelineWidth = document.getElementById("tt-timeline").scrollWidth;
    let blockCount = 0;

    function splitBlockRecursive(currentBlock, wasSplit = false) {
        const start = new Date(currentBlock.start_datetime);
        const end = new Date(currentBlock.end_datetime);
        const endOfDay = new Date(
            start.getFullYear(),
            start.getMonth(),
            start.getDate() + 1,
        );

        const startMins = start.getHours() * 60 + start.getMinutes();
        let lengthMins = (end - start) / (60 * 1000);
        const scheduleStartMins = (window.settings?.start_hour ?? 0) * 60;

        var sTime = `${formatTime(start.getHours())}:${formatTime(start.getMinutes())} `;
        var eTime = ` ${formatTime(end.getHours())}:${formatTime(end.getMinutes())}`;
        if (wasSplit) {
            sTime = `<`;
        }
        if (end > endOfDay) {
            lengthMins = (endOfDay - start) / (60 * 1000);
            eTime = `>`;
        }
        var displayTime = `${sTime}-${eTime}`;

        const el = document.createElement("div");
        el.classList.add("timetable-block", `timetable-block-${block.id}`);
        el.dataset.held = 0;
        el.dataset.blockTitle = block.title;
        el.dataset.blockTime = displayTime;
        el.dataset.blockId = block.id;
        el.dataset.blockColour = block.colour;
        el.dataset.blockLength = lengthMins;
        el.id = `timetable-block-${block.id}-${blockCount}`;

        if (window.settings.timetable_view == "horizontal") {
            const leftPx =
                ((startMins - scheduleStartMins) / minsInDay) *
                schedule.scrollWidth;
            const widthPx = (lengthMins / minsInDay) * schedule.scrollWidth;
            el.style.setProperty("--left", `${leftPx}px`);
            el.style.setProperty("--width", `${widthPx}px`);

            const topPx =
                dayMapping[`${start.toDateString().slice(4)}`] *
                (schedule.scrollHeight / dpv);
            const heightPx = schedule.scrollHeight / dpv;
            el.style.setProperty("--top", `${topPx}px`);
            el.style.setProperty("--height", `${heightPx}px`);
        } else {
            const topPx =
                ((startMins - scheduleStartMins) / minsInDay) *
                schedule.scrollHeight;
            const heightPx = (lengthMins / minsInDay) * schedule.scrollHeight;
            el.style.setProperty("--top", `${topPx}px`);
            el.style.setProperty("--height", `${heightPx}px`);

            const leftPx =
                dayMapping[`${start.toDateString().slice(4)}`] *
                (schedule.scrollWidth / dpv);
            const widthPx = schedule.scrollWidth / dpv;
            el.style.setProperty("--left", `${leftPx}px`);
            el.style.setProperty("--width", `${widthPx}px`);
        }
        el.style.setProperty(
            "--bg-colour",
            block.colour ?? window.settings?.default_block_colour ?? "#3b3d68",
        );

        const infoDiv = document.createElement("div");
        infoDiv.classList.add("block-info", "sticky");

        const titleSpan = document.createElement("span");
        titleSpan.className = "block-title";
        titleSpan.textContent = block.title;
        const timeSpan = document.createElement("span");
        timeSpan.className = "block-time";
        timeSpan.textContent = displayTime;
        infoDiv.append(titleSpan, document.createElement("br"), timeSpan);
        el.appendChild(infoDiv);
        el.dataset.date = start.toDateString().slice(3);

        const scheduleContainer = document.getElementById(
            "tt-schedule-container",
        );

        let startX = 0;
        let startY = 0;
        let startW = 0;
        let startH = 0;
        let startL = 0;
        let startT = 0;
        let snapXpx = (1 / snapX) * schedule.scrollWidth;
        let snapYpx = (1 / snapY) * schedule.scrollHeight;
        let snappedPos = 0;
        let snappedLength = 0;
        let snapUnitpx = 0;

        const onPointerDown = (e) => {
            if (e.button !== undefined && e.button !== 0) return;

            editing = true;

            if (el.dataset.held == 0) {
                if (selectedBlock) {
                    if (selectedBlock != el) {
                        selectedBlock.classList.remove("selected");
                        selectedBlock = el;
                        el.classList.add("selected");
                    }
                    startHandle.style.visibility = "hidden";
                    endHandle.style.visibility = "hidden";
                    closePopupMenu();
                } else {
                    el.classList.add("selected");
                    selectedBlock = el;
                    showHandles();

                    return;
                }
            } else {
                if (selectedBlock) {
                    if (selectedBlock != el) {
                        selectedBlock.classList.remove("selected");
                    }
                }
                selectedBlock = el;
            }

            el.style.zIndex = 5;

            startX = e.clientX;
            startY = e.clientY;
            startW = parseFloat(el.style.getPropertyValue("--width"));
            startH = parseFloat(el.style.getPropertyValue("--height"));
            startL = parseFloat(el.style.getPropertyValue("--left"));
            startT = parseFloat(el.style.getPropertyValue("--top"));
            if (el.dataset.held == 1) {
                const boundRect = el.getBoundingClientRect();
                const holding = document.getElementById("block-holding");
                startL =
                    scheduleContainer.scrollLeft +
                    holding.offsetLeft + e.pageX;
                startT =
                    scheduleContainer.scrollTop -
                    holding.offsetTop +
                    e.pageY;
                el.style.setProperty("--left", `${startL}px`);
                el.style.setProperty("--top", `${startT}px`);
                el.classList.remove("held-block");
            }

            shadow.style.setProperty("--width", `${startW}px`);
            shadow.style.setProperty("--height", `${startH}px`);
            shadow.style.setProperty(
                "--bg-colour",
                el.style.getPropertyValue("--bg-colour"),
            );

            shadow.style.setProperty("--left", `${startL}px`);
            shadow.style.setProperty("--top", `${startT}px`);

            window.addEventListener("pointermove", onPointerMove);
            window.addEventListener("pointerup", onPointerUp);
            shadow.style.visibility = "visible";
            e.preventDefault();
        };

        const onPointerMove = (e) => {
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            let newL = startL;
            let newT = startT;

            newL = startL + dx;
            newT = startT + dy;
            el.style.setProperty("--left", `${newL}px`);
            el.style.setProperty("--top", `${newT}px`);

            newL = Math.max(0, Math.min(newL, schedule.scrollWidth - startW));
            newT = Math.max(0, Math.min(newT, schedule.scrollHeight - startH));

            let snapLpx = (1 / snapX) * schedule.scrollWidth;
            let snappedL = newL - (newL % snapLpx);
            shadow.style.setProperty("--left", `${snappedL}px`);

            let snapTpx = (1 / snapY) * schedule.scrollHeight;
            let snappedT = Math.max(
                0,
                newT + startH / 2 - ((newT + startH / 2) % snapTpx),
            );
            shadow.style.setProperty("--top", `${snappedT}px`);

            if (window.settings["timetable_view"] == "horizontal") {
                snappedPos = snappedL;
                snapUnitpx = snapXpx;
                snappedLength = el.getBoundingClientRect().width;
            } else {
                snappedPos = snappedT;
                snapUnitpx = snapYpx;
                snappedLength = el.getBoundingClientRect().height;
            }

            const startFullMins = Math.ceil(snappedPos / snapUnitpx) * 10;
            const endFullMins =
                Math.ceil((snappedPos + snappedLength) / snapUnitpx) * 10; // slot size

            const startHour = Math.floor(startFullMins / 60);
            const startMin = startFullMins % 60;
            const endHour = Math.floor(endFullMins / 60);
            const endMin = endFullMins % 60;

            const lengthFullMins = endFullMins - startFullMins;

            var sTime = `${formatTime(startHour)}:${formatTime(startMin)} `;
            var eTime = ` ${formatTime(endHour)}:${formatTime(endMin)}`;
            var displayTime = `${sTime}-${eTime}`;

            const timeSpan = selectedBlock
                .getElementsByClassName("block-time")
                .item(0);

            el.dataset.edited = true;
            el.dataset.blockLength = lengthFullMins;
            timeSpan.textContent = displayTime;
        };

        const onPointerUp = (e) => {
            window.removeEventListener("pointermove", onPointerMove);
            window.removeEventListener("pointerup", onPointerUp);

            el.dataset.blockTime = timeSpan.textContent;
            shadow.style.visibility = "hidden";

            el.style.zIndex = 0;

            const holding = document.getElementById("block-holding");
            if (holding.classList.contains("hovered")) {
                holdBlock(el);

                return;
            }

            let snapL = parseFloat(el.style.getPropertyValue("--left"));
            let snapLpx = (1 / snapX) * schedule.scrollWidth;
            let snappedL = snapL - (snapL % snapLpx);
            el.style.setProperty("--left", `${snappedL}px`);

            let snapT = parseFloat(el.style.getPropertyValue("--top"));
            let snapTpx = (1 / snapY) * schedule.scrollHeight;
            let snappedT = Math.max(
                0,
                snapT + startH / 2 - ((snapT + startH / 2) % snapTpx),
            );
            el.style.setProperty("--top", `${snappedT}px`);

            if (el.dataset.held == 1) {
                el.dataset.held = 0;

                const holdingPen = document.getElementById("block-holding");
                holdingPen.removeChild(el);
                schedule.append(el);
            }

            showHandles();
        };

        el.addEventListener("pointerdown", onPointerDown);

        function showHandles() {
            const leftPx = parseFloat(el.style.getPropertyValue("--left"));
            const topPx = parseFloat(el.style.getPropertyValue("--top"));
            if (window.settings.timetable_view == "horizontal") {
                const heightPx = el.style.getPropertyValue("--height");
                const widthPx = parseFloat(
                    el.style.getPropertyValue("--width"),
                );
                const handleWidthPx = 15;
                startHandle.style.setProperty(
                    "--left",
                    `${leftPx - handleWidthPx}px`,
                );
                startHandle.style.setProperty("--top", `${topPx}px`);

                endHandle.style.setProperty("--left", `${leftPx + widthPx}px`);
                endHandle.style.setProperty("--top", `${topPx}px`);

                startHandle.style.setProperty("--height", heightPx);
                startHandle.style.setProperty("--width", `${handleWidthPx}px`);

                endHandle.style.setProperty("--height", heightPx);
                endHandle.style.setProperty("--width", `${handleWidthPx}px`);
            } else {
                const heightPx = el.style.getPropertyValue("--height");
                const widthPx = parseFloat(
                    el.style.getPropertyValue("--width"),
                );
                const handleHeightPx = 15;
                startHandle.style.setProperty("--left", `${leftPx}px`);
                startHandle.style.setProperty(
                    "--top",
                    `${topPx - handleHeightPx}px`,
                );

                endHandle.style.setProperty("--left", `${leftPx}px`);
                endHandle.style.setProperty("--top", `${topPx + heightPx}px`);

                startHandle.style.setProperty(
                    "--height",
                    `${handleHeightPx}px`,
                );
                startHandle.style.setProperty("--width", widthPx);

                endHandle.style.setProperty("--height", `${handleHeightPx}px`);
                endHandle.style.setProperty("--width", widthPx);
            }

            startHandle.style.visibility = "visible";
            endHandle.style.visibility = "visible";
        }

        pieces.push(el);

        if (end > endOfDay) {
            blockCount++;
            const nextBlock = {
                ...currentBlock,
                start_datetime: endOfDay.toISOString(),
            };
            splitBlockRecursive(nextBlock, true);
        } else if (blockCount > 0) {
            document.getElementById(
                `timetable-block-${block.id}-0`,
            ).dataset.lastBlockId = blockCount;
        }
    }

    splitBlockRecursive(block);
    return pieces;
}

async function renderTimetable() {
    const payload = await fetchPayload();
    const blocks = payload.blocks;
    const schedule = document.getElementById("tt-schedule");

    spawnShadowBlock();
    spawnBlockHandles();

    for (const block of blocks) {
        const pieces = splitBlock(block);
        for (const el of pieces) {
            schedule.append(el);
        }
    }
}

async function clearTimetable() {
    // TODO : Add clear timetable functionality. Target all .timetable-block elements?
}

async function saveTimetable() {
    const blocks = document.getElementsByClassName("timetable-blocks");

    var editedBlocks = {};

    for (block of blocks) {
        if (!block.dataset.edited) return;
        const bInfo = block.id.split("-");
        if (bInfo != 0) return; // check if it is the starting block
        const bId = bInfo[2];

        editedBlocks[bId] = {};

        const timeString = block.dataset.blockTime.split("-");
        editedBlocks[bId]["start_time"] = timeString[0];
        editedBlocks[bId]["end_time"] = timeString[1];

        if (block.dataset.lastBlockId) {
            const lastBlock = document.getElementById(`timetable-block-${bId}-${lastBlockId}`)
            const lastTimeString = lastBlock.dataset.blockTime.split("-");
            editedBlocks[bId]["end_time"] = lastTimeString[1];
        }


    }
}

function prevDate() {
    console.log("previous");
    const msInDay = 24 * 60 * 60 * 1000;
    displayDate = new Date(
        displayDate.getTime() - msInDay * window.settings["days_per_view"],
    );
    rebuildTimetable();
}

function currentDate() {
    displayDate = new Date();
    rebuildTimetable();
}

function nextDate() {
    console.log("next");
    const msInDay = 24 * 60 * 60 * 1000;
    displayDate = new Date(
        displayDate.getTime() + msInDay * window.settings["days_per_view"],
    );
    rebuildTimetable();
}

function buildTimetable() {
    document.documentElement.style.setProperty(
        "--days",
        window.settings["days_per_view"],
    );
    generateDays(); // generate first column of the timetable
    generateTimeline(); // generate top row of the timetable
    updateTime(); // set the timetable corner clock
    buildGrid(); // generate grid
    alignTimeMarker(); // make sure time marker is in the right place

    document
        .getElementById("timetable-container")
        .dispatchEvent(new Event("finishedBuilding"));
}

function rebuildTimetable() {
    document.documentElement.style.setProperty(
        "--days",
        window.settings["days_per_view"],
    );
    generateDays(); // generate first column of the timetable
    updateTime();
    renderTimetable().catch((err) =>
        console.error("Timetable render failed:", err),
    );
}

function initHolding() {
    const holding = document.getElementById("block-holding");
    window.addEventListener("pointermove", (e) => {
        if (
            e.pageX >= holding.offsetLeft &&
            e.pageX <= holding.offsetLeft + holding.offsetWidth &&
            e.pageY >= holding.offsetTop &&
            e.pageY <= holding.offsetTop + holding.offsetHeight
        ) {
            holding.classList.add("hovered");
        } else {
            holding.classList.remove("hovered");
        }
    });
}

/**
 * Initialise the timetable
 */
async function initTimetable() {
    // Build timetable (actual html and timetable divs)
    window.settings = await fetchSettings();
    displayDate = displayDate || null;

    if (window.settings.timetable_view == "horizontal") {
        snapY = window.settings["days_per_view"];
        snapX = 144;
    } else {
        snapY = 144;
        snapX = window.settings["days_per_view"];
    }

    initHolding();
    buildTimetable();

    window.pageIntervals.temporary.push(
        setInterval(alignTimeMarker, 60 * 1000),
    ); // update the time marker every 60 seconds
    window.pageIntervals.temporary.push(setInterval(updateTime, 5 * 1000)); // set the timetable corner clock
    alignTimetimetableView(); // scroll timetable to the current time

    // Render timetable (events, block, content)
    renderTimetable().catch((err) =>
        console.error("Timetable render failed:", err),
    );
    window.addEventListener("resize", closePopupMenu);
    window.addEventListener("scroll", closePopupMenu);

    const scheduleContainer = document.getElementById("tt-schedule-container");
    scheduleContainer.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        const block = e.target.closest(".timetable-block");
        if (!block) return;
        e.stopPropagation();
        showPopupMenu(block, e);
        return false;
    });

    document
        .getElementById("backdrop")
        .addEventListener("click", closePopupMenu);
    document.addEventListener("keydown", (e) => {
        const popupMenu = document.getElementById("popup-menu");
        if (!popupMenu) return;
        if (e.key === "Escape" && popupMenu.classList.contains("open")) {
            closePopupMenu();
        }
    });

    const closeTabConfirmation = (e) => {
        if (editing) {
            if (
                confirm(
                    (message =
                        "Timetable has been edited. Are you sure you want to exit?"),
                )
            ) {
                editing = false;
                window.removeEventListener(
                    "beforeunload",
                    closeTabConfirmation,
                );
            } else {
                e.preventDefault();
            }
        }
    };

    window.addEventListener("beforeunload", closeTabConfirmation);
}

initTimetable();
