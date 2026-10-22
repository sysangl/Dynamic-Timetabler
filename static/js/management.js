itemForms = document.getElementById('item-forms')
function toggleForms() {
    console.log('Toggling forms')
    document.getElementById('backdrop').classList.toggle('hidden')
    itemForms.classList.toggle('hidden')
}

async function fetchTimetableItems() {
    const response = await fetch(`/api/timetable`, {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    return await response.json()
}

async function generateItemTable() {
    const timetableItems = await fetchTimetableItems()
    const itemTable = document.getElementById('item-table-body')
    itemTable.innerHTML = "";
    let itemCount = 0

    for (const [itemType, items] of Object.entries(timetableItems)) {
        for (const item of items) {
            const row = document.createElement('tr');
            row.id = `${itemType}-${item.id}`
            const itemTypeText = document.createElement('td')
            itemTypeText.textContent = itemType.slice(0,-1).toLocaleUpperCase()
            const itemTitleText = document.createElement('td')
            itemTitleText.textContent = item.title
            const itemStart = document.createElement('td')
            const startDateTime = new Date(item.start_datetime)
            const sDate = document.createElement('p')
            sDate.textContent = startDateTime.toLocaleDateString()
            const sTime = document.createElement('p')
            sTime.textContent = startDateTime.toLocaleTimeString().replace(':00 ',' ')
            itemStart.append(sDate,sTime)

            const itemEnd = document.createElement('td')
            const endDateTime = new Date(item.end_datetime)
            const eDate = document.createElement('p')
            eDate.textContent = endDateTime.toLocaleDateString()
            const eTime = document.createElement('p')
            eTime.textContent = endDateTime.toLocaleTimeString().replace(':00 ',' ')
            itemEnd.append(eDate,eTime)

            const itemStatus = document.createElement('td')
            itemStatus.textContent = 'Uncompleted'

            row.append(itemTypeText, itemTitleText, itemStart, itemEnd, itemStatus)
            itemTable.append(row)
            itemCount += 1
        }
    }
    document.getElementById('item-counter').textContent = itemCount;
}


async function setupManagement () {
    let settings = await fetchSettings()
    const now = new Date();
    const future = new Date(now.getTime() + settings.default_block_length * 60 * 1000);

    const sDate = now.toISOString().split('T')[0];
    const eDate = future.toISOString().split('T')[0];

    const sHours   = String(now.getHours()).padStart(2, '0');
    const sMinutes = String(now.getMinutes()).padStart(2, '0');
    const sTime = `${sHours}:${sMinutes}`;  

    const eHours   = String(future.getHours()).padStart(2, '0');
    const eMinutes = String(future.getMinutes()).padStart(2, '0');
    const eTime = `${eHours}:${eMinutes}`;  

    document.getElementById('sdate').value = sDate;
    document.getElementById('edate').value = eDate;

    document.getElementById('stime').value = sTime;
    document.getElementById('etime').value = eTime;

    generateItemTable();
}
setupManagement();