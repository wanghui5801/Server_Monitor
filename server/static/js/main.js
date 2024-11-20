const socket = io();

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function createTooltip(cell, content) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.innerHTML = content;
    
    // Get progress bar element
    const progressBar = cell.querySelector('.progress-bar');
    
    // Listen to mouse events on the entire progress bar
    progressBar.addEventListener('mouseenter', () => {
        tooltip.style.opacity = '0';
        cell.appendChild(tooltip);
        requestAnimationFrame(() => {
            tooltip.style.opacity = '1';
        });
    });

    progressBar.addEventListener('mouseleave', (e) => {
        // Check if really left the progress bar area
        const rect = progressBar.getBoundingClientRect();
        const isStillInside = (
            e.clientX >= rect.left &&
            e.clientX <= rect.right &&
            e.clientY >= rect.top &&
            e.clientY <= rect.bottom
        );
        
        if (!isStillInside) {
            tooltip.style.opacity = '0';
            tooltip.addEventListener('transitionend', () => {
                if (tooltip.parentNode === cell) {
                    cell.removeChild(tooltip);
                }
            });
        }
    });
}

function updateTable(data) {
    const tbody = document.getElementById('vps-data');
    const isMobile = window.matchMedia("(max-width: 768px)").matches;
    
    const newRows = Object.values(data).map(client => {
        const row = document.createElement('tr');
        
        if (isMobile) {
            row.innerHTML = `
                <td><span class="status ${client.status.type}">${client.status.text}</span></td>
                <td>${client.node_name}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${client.cpu}%"></div>
                        <div class="progress-text">${client.cpu}%</div>
                    </div>
                </td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${client.memory}%"></div>
                        <div class="progress-text">${client.memory}%</div>
                    </div>
                </td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${client.disk}%"></div>
                        <div class="progress-text">${client.disk}%</div>
                    </div>
                </td>
            `;
        } else {
            row.innerHTML = `
                <td><span class="status ${client.status.type}">${client.status.text}</span></td>
                <td>${client.node_name}</td>
                <td>${client.type}</td>
                <td><span class="fi fi-${client.location.country_code}"></span></td>
                <td>${client.uptime} days</td>
                <td>${client.load.toFixed(2)}</td>
                <td>${formatBytes(client.network_speed.up)}/s | ${formatBytes(client.network_speed.down)}/s</td>
                <td>${client.traffic.sent.toFixed(2)}G | ${client.traffic.received.toFixed(2)}G</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${client.cpu}%"></div>
                        <div class="progress-text">${client.cpu}%</div>
                    </div>
                </td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${client.memory}%"></div>
                        <div class="progress-text">${client.memory}%</div>
                    </div>
                </td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${client.disk}%"></div>
                        <div class="progress-text">${client.disk}%</div>
                    </div>
                </td>
                <td><span class="system-icon ${client.os_type || 'unknown'}"></span></td>
            `;
        }
        
        // Add tooltip
        const cpuCell = row.cells[isMobile ? 2 : 8];
        const memCell = row.cells[isMobile ? 3 : 9];
        const diskCell = row.cells[isMobile ? 4 : 10];
        
        createTooltip(cpuCell, `${client.system_info.cpu.model}`);
        createTooltip(memCell, `${formatBytes(client.system_info.memory_total)}`);
        createTooltip(diskCell, `${formatBytes(client.system_info.disk_total)}`);
        
        return row;
    });

    tbody.innerHTML = '';
    newRows.forEach(row => tbody.appendChild(row));
}

socket.on('status_update', (data) => {
    const sortedData = Object.values(data).sort((a, b) => {
        return a.node_name.localeCompare(b.node_name, undefined, {
            sensitivity: 'base',
            numeric: true
        });
    });
    updateTable(sortedData);
});

// Initial data load
fetch('/get_status')
    .then(response => response.json())
    .then(data => {
        const sortedData = Object.values(data).sort((a, b) => {
            return a.node_name.localeCompare(b.node_name, undefined, {
                sensitivity: 'base',
                numeric: true
            });
        });
        updateTable(sortedData);
    });
