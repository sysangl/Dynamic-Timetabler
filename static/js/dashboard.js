async function fetchUpcoming() {
    const response = await fetch(
        `/api/timetable/upcoming/`,
        {
            method: "GET",
            headers: {
                Accept: "application/json",
            },
        },
    );

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
    }
    console.log(response)
    return response.json();
}

async function generateUpcomingTable() {
    const upcomingTable = document.getElementById('upcoming-table-body')
    const upcoming = await fetchUpcoming();
    for (const [key, items] of Object.entries(upcoming)) {
        if (key=='status') {continue};
        const dateText = document.createElement('tr')
        const dateSpan = document.createElement('span')
        dateSpan.classList.add('date')
        dateSpan.textContent = key
        dateText.append(dateSpan)
        upcomingTable.append(dateText)
        for (const item of items) {
            const start = new Date(item.start_datetime);
            const end = new Date(item.end_datetime);
            var sTime = `${formatTime(start.getHours())}:${formatTime(start.getMinutes())} `;
            var eTime = ` ${formatTime(end.getHours())}:${formatTime(end.getMinutes())}`;
            var displayTime = `${sTime}-${eTime}`;
    
            const row = document.createElement('tr')
            const div = document.createElement('div')
            div.classList.add('upcoming-block')
            div.style.setProperty('--bg-colour', item.colour)
            const titleSpan = document.createElement('span')
            titleSpan.classList.add('title')
            titleSpan.textContent = item.title
            const timeSpan = document.createElement('span')
            timeSpan.classList.add('time')
            timeSpan.textContent = displayTime
            div.append(titleSpan,document.createElement('br'),timeSpan)
            row.append(div)
            upcomingTable.append(row)

        }

        
    }

}

async function initDashboard() {
    generateUpcomingTable();
}

initDashboard();