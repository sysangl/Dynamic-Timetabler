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
    const backdrop = document.getElementById("backdrop");
    const popupMenu = document.getElementById("popup-menu");
    const popupBlockTitle = document.getElementById("popup-block-title");
    const popupBlockTime = document.getElementById("popup-block-time");
    const popupBlockInfo = document.getElementById("popup-block-info");

    const alreadyOpen =
        popupMenu.classList.contains("open") &&
        target === popupMenu._currentTarget;
    if (alreadyOpen) {
        closePopupMenu();
        return;
    }

    if (
        e.pageY + popupMenu.clientHeight >=
        document.documentElement.clientHeight
    ) {
        popupMenu.style.bottom = "10px";
        popupMenu.style.top = "unset";
    } else {
        popupMenu.style.bottom = "unset";
        popupMenu.style.top = `${e.pageY}px`;
    }

    // popupMenu.style.left = `${bRect.left + window.scrollX}px`;
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

    popupBlockTitle.textContent = target.dataset.blockTitle;
    popupBlockTime.textContent = target.dataset.blockTime;
    popupBlockInfo.style.background = target.dataset.blockColour;

    popupMenu._currentTarget = target;
    popupMenu.classList.add("open");
    backdrop.classList.add("active");
}

function closePopupMenu() {
    const popupMenu = document.getElementById("popup-menu");
    const backdrop = document.getElementById("backdrop");
    if (!popupMenu || !backdrop) return;
    popupMenu.classList.remove("open");
    backdrop.classList.remove("active");
    if (popupMenu._currentTarget) {
        delete popupMenu._currentTarget;
    }
}

async function deleteBlock() {
    const popupMenu = document.getElementById("popup-menu");
    const blockId = popupMenu._currentTarget.dataset.blockId;
    const response = await fetch(`/api/timetable/block/${blockId}`, {
        method: "DELETE",
    });
    document
        .querySelectorAll(`#timetable-block-${blockId}`)
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
    startHandle.id = 'start-handle';
    endHandle.id = 'end-handle';
    startHandle.classList.add('block-handle');
    endHandle.classList.add('block-handle');
    startHandle.style.visibility = 'hidden';
    endHandle.style.visibility = 'hidden';
    document.getElementById('tt-schedule').append(startHandle, endHandle)

    const handleWidthPx = 15

    const scheduleContainer = document.getElementById('tt-schedule-container')
    const schedule = document.getElementById('tt-schedule')

    const startDrag = (e) => {
        const elRect = startHandle.getBoundingClientRect();
        dragOffsetX = e.clientX - elRect.left;
        dragOffsetY = e.clientY - elRect.top;

        startHandleDragging = true;
    }

    const stopDrag = (e) => {
        if (startHandleDragging) {
            var x =
                e.clientX +
                scheduleContainer.scrollLeft -
                scheduleContainer.offsetLeft -
                dragOffsetX;

            var snapXpx = (1 / snapX) * schedule.scrollWidth;

            var snappedX = x - (x % snapXpx);

            startHandle.style.setProperty("--left", `${snappedX}px`);
            const timeSpan = selectedBlock.getElementsByClassName('block-time').item(0)
            timeSpan.textContent = selectedBlock.dataset.blockTime
            // selectedBlock.dataset.blockTime = selectedBlocktimeSpan.textContent;
        }
        startHandleDragging = false;
    };


    startHandle.onmousedown = (e) => {
        e.preventDefault();
        startDrag(e)
    };

    startHandle.onmouseup = (e) => {
        stopDrag(e)
    }


    startHandle.onmousemove = (e) => {
        if (startHandleDragging) {
            const el = selectedBlock
            var x =
                e.clientX +
                scheduleContainer.scrollLeft -
                scheduleContainer.offsetLeft -
                dragOffsetX;

            var snapXpx = (1 / snapX) * schedule.scrollWidth;

            var snappedX = x - (x % snapXpx);

            startHandle.style.setProperty("--left", `${x}px`);
            el.style.setProperty("--left",`${x+handleWidthPx}px`)

            el.style.setProperty('--width', `${parseFloat(endHandle.style.getPropertyValue('--left'))-x}px`)

            const elBound = el.getBoundingClientRect()

            const startFullMins = Math.round(snappedX / snapXpx) * 10
            const endFullMins = Math.round((snappedX / snapXpx) + elBound.width) * 10; // slot size

            
            const startHour = Math.floor(startFullMins / 60);
            const startMin = startFullMins % 60;
            const endHour = Math.floor(endFullMins / 60);
            const endMin = endFullMins % 60;

            const lengthFullMins = endFullMins - startFullMins
            
            var sTime = `${formatTime(startHour)}:${formatTime(startMin)} `;
            var eTime = ` ${formatTime(endHour)}:${formatTime(endMin)}`;
            var displayTime = `${sTime}-${eTime}`;

            const timeSpan = selectedBlock.getElementsByClassName('block-time').item(0)



            el.dataset.blockLength = lengthFullMins;
            timeSpan.textContent = displayTime



        }
    };



}

/**
 * Creates a block and splits it if it goes over visible time.
 * Returns an array of HTMLDivElements
 *
 * @param {Object} block
 * @returns {Array[HTMLDivElement]}
 */
function splitBlock(block) {
    const startHandle = document.getElementById('start-handle');
    const endHandle = document.getElementById('end-handle');
    const schedule = document.getElementById("tt-schedule");
    const pieces = [];
    const minsInDay = 24 * 60;
    const dpv = window.settings["days_per_view"];
    const shadow = document.getElementById("shadow-block");
    const timelineHeight = document.getElementById("tt-timeline").scrollHeight;
    const timelineWidth = document.getElementById("tt-timeline").scrollWidth;

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
        el.classList.add("timetable-block");
        el.dataset.blockTitle = block.title;
        el.dataset.blockTime = displayTime;
        el.dataset.blockId = block.id;
        el.dataset.blockColour = block.colour;
        el.dataset.blockLength = lengthMins
        el.id = `timetable-block-${block.id}`;

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



        const startDrag = (e) => {
            const elRect = el.getBoundingClientRect();
            dragOffsetX = e.clientX - elRect.left;
            dragOffsetY = e.clientY - elRect.top;

            shadow.style.visibility = "visible";

            shadow.style.setProperty(
                "--width",
                el.style.getPropertyValue("--width"),
            );
            shadow.style.setProperty(
                "--height",
                el.style.getPropertyValue("--height"),
            );
            shadow.style.setProperty(
                "--bg-colour",
                el.style.getPropertyValue("--bg-colour"),
            );

            startHandle.style.visibility = 'visible';
            endHandle.style.visibility = 'visible';



            blockDragging = true;
        }
        

        const stopDrag = (e) => {
            if (blockDragging) {
                var x =
                    e.clientX +
                    scheduleContainer.scrollLeft -
                    scheduleContainer.offsetLeft -
                    dragOffsetX;
                var y =
                    e.clientY +
                    scheduleContainer.scrollTop -
                    scheduleContainer.offsetTop -
                    dragOffsetY;

                var snapXpx = (1 / snapX) * schedule.scrollWidth;
                var snapYpx = (1 / snapY) * schedule.scrollHeight;

                var snappedX = x - (x % snapXpx);
                var snappedY = y - (y % snapYpx);

                el.style.setProperty("--left", `${snappedX}px`);
                el.style.setProperty("--top", `${snappedY}px`);

                el.dataset.blockTime = timeSpan.textContent;
            }
            blockDragging = false;
            shadow.style.visibility = "hidden";

            el.style.zIndex = 1;
        };

        function showHandles() {
                const leftPx = parseFloat(el.style.getPropertyValue("--left"))
                const topPx = parseFloat(el.style.getPropertyValue("--top"))
                if (window.settings.timetable_view == "horizontal") {
                    const heightPx = el.style.getPropertyValue("--height")
                    const widthPx = parseFloat(el.style.getPropertyValue("--width"))
                    const handleWidthPx = 15
                    startHandle.style.setProperty("--left", `${leftPx - handleWidthPx}px`);
                    startHandle.style.setProperty("--top", `${topPx}px`);
                    
                    endHandle.style.setProperty("--left", `${leftPx + widthPx}px`);
                    endHandle.style.setProperty("--top", `${topPx}px`);
    
                    startHandle.style.setProperty("--height", heightPx)
                    startHandle.style.setProperty("--width", `${handleWidthPx}px`)
    
                    endHandle.style.setProperty("--height", heightPx)
                    endHandle.style.setProperty("--width", `${handleWidthPx}px`)
    
                } else {
                    const heightPx = el.style.getPropertyValue("--height")
                    const widthPx = parseFloat(el.style.getPropertyValue("--width"))
                    const handleHeightPx = 15
                    startHandle.style.setProperty("--left", `${leftPx}px`);
                    startHandle.style.setProperty("--top", `${topPx - handleHeightPx}px`);
                    
                    endHandle.style.setProperty("--left", `${leftPx}px`);
                    endHandle.style.setProperty("--top", `${topPx + heightPx}px`);
                
                    startHandle.style.setProperty("--height", `${handleHeightPx}px`)
                    startHandle.style.setProperty("--width", widthPx)
    
                    endHandle.style.setProperty("--height", `${handleHeightPx}px`)
                    endHandle.style.setProperty("--width", widthPx)
                }
    
                startHandle.style.visibility = 'visible';
                endHandle.style.visibility = 'visible';
        }

        el.onmousedown = (e) => {
            if (!el.classList.contains('selected')) {return}
            e.preventDefault();
            startDrag(e)
        };

        el.ondblclick = (e) => {
            el.classList.add('selected')
            startDrag(e)
        }


        el.onclick = (e) => {
            if (blockDragging) {
                stopDrag(e)
                // el.classList.remove('selected')

                showHandles();
            } else {
                if (selectedBlock) {
                    selectedBlock.classList.remove('selected')
                    selectedBlock = null
                }
                el.classList.add('selected')
                selectedBlock = el

                showHandles();

            }


        };
        el.onmouseleave = stopDrag;

        el.onmousemove = (e) => {
            if (blockDragging) {
                var x =
                    e.clientX +
                    scheduleContainer.scrollLeft -
                    scheduleContainer.offsetLeft -
                    dragOffsetX;
                var y =
                    e.clientY +
                    scheduleContainer.scrollTop -
                    scheduleContainer.offsetTop -
                    dragOffsetY;

                if (window.settings.timetable_view == "horizontal") {
                    el.style.setProperty("--left", `${x}px`);
                    el.style.setProperty("--top", `${y - timelineHeight}px`);
                } else {
                    el.style.setProperty("--left", `${x - timelineWidth}px`);
                    el.style.setProperty("--top", `${y}px`);
                }

                el.style.zIndex = 5;

                var snapXpx = (1 / snapX) * schedule.scrollWidth;
                var snapYpx = (1 / snapY) * schedule.scrollHeight;

                var snappedX = x - (x % snapXpx);
                var snappedY = y - (y % snapYpx);

                shadow.style.setProperty("--left", `${snappedX}px`);
                shadow.style.setProperty("--top", `${snappedY}px`);


                if (window.settings.timetable_view == "horizontal") {
                    const heightPx = el.style.getPropertyValue("--height")

                    shadow.style.setProperty(
                        "--height",
                        heightPx
                    );


                } else {
                    const widthPx = parseFloat(el.style.getPropertyValue("--width"))

                    shadow.style.setProperty(
                        "--width",
                        widthPx
                    );
                }


                let startFullMins = 0;
                if (window.settings.timetable_view == "horizontal") {
                    startFullMins = Math.round(snappedX / snapXpx) * 10; // slot size
                } else {
                    startFullMins = Math.round(snappedY / snapYpx) * 10; // slot size
                }
                
                const lengthMins = parseInt(el.dataset.blockLength);
                const startHour = Math.floor(startFullMins / 60);
                const startMin = startFullMins % 60;
                const endHour = Math.floor((startFullMins + lengthMins) / 60);
                const endMin = (startFullMins + lengthMins) % 60;
                
                var sTime = `${formatTime(startHour)}:${formatTime(startMin)} `;
                var eTime = ` ${formatTime(endHour)}:${formatTime(endMin)}`;
                var displayTime = `${sTime}-${eTime}`;

                timeSpan.textContent = displayTime;

                startHandle.style.visibility = 'hidden';
                endHandle.style.visibility = 'hidden';

            }
        };


        pieces.push(el);

        if (end > endOfDay) {
            const nextBlock = {
                ...currentBlock,
                start_datetime: endOfDay.toISOString(),
            };
            splitBlockRecursive(nextBlock, true);
        }
    }

    splitBlockRecursive(block);
    return pieces;
}

async function renderTimetable() {
    const payload = await fetchPayload();
    const blocks = payload.blocks;
    // const getDayContainer = (date) =>
    //     document.querySelector(`[data-date="${date}"]`);
    const schedule = document.getElementById("tt-schedule");
    // const fragmentMap = new Map();

    spawnShadowBlock();
    spawnBlockHandles();

    for (const block of blocks) {
        const pieces = splitBlock(block);
        for (const el of pieces) {
            // const date = el.dataset.date;
            // if (!fragmentMap.has(date)) {
            //     fragmentMap.set(date, document.createDocumentFragment());
            // }
            // fragmentMap.get(date).appendChild(el);
            schedule.append(el);
        }
    }

    // fragmentMap.forEach((frag, date) => {
    //     const dayContainer = getDayContainer(date);
    //     if (dayContainer) {
    //         dayContainer.appendChild(frag);
    //     }
    // });
}

async function clearTimetable() {
    const dayContainers = Array.from({ length: 7 }, (_, i) => {
        // The DOM has: <section id="day-container-Mon"><div class="day-inner"></div></section>
        const container = document.getElementById(
            `day-container-${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i]}`,
        );
        return container;
    });
    dayContainers.forEach((container) => {
        container.children.forEach((child) => child.remove());
    });
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
}

initTimetable();
