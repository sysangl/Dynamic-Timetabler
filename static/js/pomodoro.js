

function decSession(id) {
    window.currentPomos[id].sessionSeconds = clamp(window.currentPomos[id].sessionSeconds-60,1,Infinity)
    document.getElementById('session-mins').textContent = Math.floor(window.currentPomos[id].sessionSeconds/60)

    if (window.currentPomos[id].running) return;
    document.getElementById('remaining-mins').textContent = Math.floor(window.currentPomos[id].sessionSeconds/60)
}

function incSession(id) {
    window.currentPomos[id].sessionSeconds = clamp(window.currentPomos[id].sessionSeconds+60,1,Infinity)
    document.getElementById('session-mins').textContent = Math.floor(window.currentPomos[id].sessionSeconds/60)

    if (window.currentPomos[id].running) return;
    document.getElementById('remaining-mins').textContent = Math.floor(window.currentPomos[id].sessionSeconds/60)
}

function decBreak(id) {
    window.currentPomos[id].sessionSeconds = clamp(window.currentPomos[id].breakSeconds-60,0,Infinity)
    document.getElementById('break-mins').textContent = Math.floor(window.currentPomos[id].breakSeconds/60)
}

function incBreak(id) {
    window.currentPomos[id].sessionSeconds = clamp(window.currentPomos[id].breakSeconds+60,0,Infinity)
    document.getElementById('break-mins').textContent = Math.floor(window.currentPomos[id].breakSeconds/60)
}

function updateTime(id) {
    document.getElementById('remaining-mins').textContent = `${Math.floor(window.currentPomos[id].currentSeconds/60)}:${formatTime(Math.floor(window.currentPomos[id].currentSeconds%60))}`
}

function newPomo(id) {
    window.currentPomos[id] = {}
    window.currentPomos[id].sessionSeconds = 30*60
    window.currentPomos[id].breakSeconds = 15*60
    window.currentPomos[id].currentSeconds = window.currentPomos[id].sessionSeconds
    window.currentPomos[id].running = false
    window.currentPomos[id].intervalId = null
    window.currentPomos[id].state = 'Session'

    document.getElementById('session-mins').textContent = Math.floor(window.currentPomos[id].sessionSeconds/60)
    document.getElementById('break-mins').textContent = Math.floor(window.currentPomos[id].breakSeconds/60)
    document.getElementById('remaining-mins').textContent = Math.floor(window.currentPomos[id].sessionSeconds/60)
}

function togglePomo(id) {
    if (window.currentPomos[id].running) {
        window.clearInterval(window.currentPomos[id].intervalId)
        window.currentPomos[id].running = false
    } else {
        window.currentPomos[id].currentSeconds = window.currentPomos[id].sessionSeconds
        window.currentPomos[id].running = true
        updateTime(1)
        window.currentPomos[id].intervalId = window.setInterval(()=>{
            window.currentPomos[id].currentSeconds -= 1;
            updateTime(id);
            if (window.currentPomos[id].currentSeconds <= 0) {
                if (window.currentPomos[id].state == 'Session') {
                    window.currentPomos[id].currentSeconds = window.currentPomos[id].breakSeconds
                    window.currentPomos[id].state == 'Break'
                    document.getElementById('pomo-timer').style.borderColor = "rgb(0, 164, 10)"
                    new Notification('Session ended. Break time!')
                } else if (window.currentPomos[id].state == 'Break') {
                    window.currentPomos[id].currentSeconds = window.currentPomos[id].sessionSeconds
                    window.currentPomos[id].state == 'Session'
                    document.getElementById('pomo-timer').style.borderColor = "rgb(164, 0, 0)"
                    new Notification('Break ended.')
                } else {
                    pomoEnded(id)
                    window.clearInterval(window.currentPomos[id].intervalId)
                }
                document.getElementById('pomo-state').textContent = window.currentPomos[id].state
            }


        }, 1000)
    }
}

function pomoEnded(id) {
    console.log(id,'ended')
    window.currentPomos[id].running = false
}

async function initPomo() {
    const settings = window.settings;

    window.currentPomos = window.currentPomos || {}
    newPomo(1)

    document.getElementById('pomo-timer').onclick = () => {togglePomo(1)}
}

initPomo();