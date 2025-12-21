// Video Monitoring Module
let currentVideo = null;
let currentViolations = [];
let player = null;
let timelineViolations = [];

// API endpoints
const API_BASE_URL = window.location.origin;
const API_VIOLATIONS = `${API_BASE_URL}/api/violations`;
const API_VIDEOS = `${API_BASE_URL}/api/videos`;
const API_EVIDENCE_VIDEOS = `${API_BASE_URL}/evidence/videos`;
const API_EVIDENCE_IMAGES = `${API_BASE_URL}/evidence/images`;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeVideoPlayer();
    loadVideos();
    setInterval(updateVideoStats, 5000); // Update stats every 5 seconds
});

// Initialize Plyr video player
function initializeVideoPlayer() {
    player = new Plyr('#player', {
        settings: ['quality', 'speed', 'loop'],
        speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
        controls: ['play', 'progress', 'current-time', 'mute', 'volume', 'settings', 'fullscreen']
    });

    // Update current time display
    player.on('timeupdate', function() {
        updateCurrentTimeDisplay();
        updateTimelineIndicator();
    });

    // Update duration when video loads
    player.on('loadedmetadata', function() {
        updateDurationDisplay();
        renderTimeline();
    });

    // Handle playback rate changes
    document.getElementById('playbackRate').addEventListener('input', function(e) {
        const rate = parseFloat(e.target.value);
        player.speed = rate;
        document.getElementById('rateLabel').textContent = `${rate}x`;
    });
}

// Load video list from API
async function loadVideos() {
    try {
        const response = await fetch(API_VIDEOS);
        if (!response.ok) throw new Error('Failed to fetch videos');
        
        const videos = await response.json();
        displayVideoList(videos);
        updateVideoStats(videos);
        
        // Select first video if available
        if (videos.length > 0 && !currentVideo) {
            selectVideo(videos[0].name);
        }
        
        updateAPIStatus(true);
    } catch (error) {
        console.error('Error loading videos:', error);
        updateAPIStatus(false);
        showNotification('Failed to load videos', 'danger');
    }
}

// Display video list
function displayVideoList(videos) {
    const videoList = document.getElementById('videoList');
    videoList.innerHTML = '';
    
    videos.forEach(video => {
        const videoItem = document.createElement('a');
        videoItem.href = '#';
        videoItem.className = 'list-group-item list-group-item-action video-card';
        videoItem.onclick = () => selectVideo(video.name);
        
        const fileName = video.name;
        const fileSize = formatFileSize(video.size);
        const created = new Date(video.created * 1000).toLocaleDateString();
        
        videoItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1"><i class="bi bi-play-circle"></i> ${fileName}</h6>
                    <small class="text-muted">${fileSize} • ${created}</small>
                </div>
                <span class="badge bg-primary rounded-pill">▶</span>
            </div>
        `;
        
        videoList.appendChild(videoItem);
    });
    
    document.getElementById('videoCount').textContent = videos.length;
}

// Select and load a video
async function selectVideo(videoName) {
    try {
        currentVideo = videoName;
        
        // Update UI
        document.getElementById('currentVideoName').textContent = videoName;
        document.querySelectorAll('.video-card').forEach(card => {
            card.classList.remove('active');
        });
        
        // Load video into player
        const videoUrl = `${API_EVIDENCE_VIDEOS}/${videoName}`;
        player.source = {
            type: 'video',
            sources: [{
                src: videoUrl,
                type: 'video/mp4'
            }]
        };
        
        // Load violations for this video
        await loadViolationsForVideo(videoName);
        
        // Load video metadata
        await loadVideoMetadata(videoName);
        
        showNotification(`Loaded video: ${videoName}`, 'success');
    } catch (error) {
        console.error('Error selecting video:', error);
        showNotification('Failed to load video', 'danger');
    }
}

// Load violations for selected video
async function loadViolationsForVideo(videoName) {
    try {
        const response = await fetch(`${API_VIOLATIONS}`);
        if (!response.ok) throw new Error('Failed to fetch violations');
        
        const allViolations = await response.json();
        
        // Filter violations for this video
        currentViolations = allViolations.filter(violation => {
            return violation.video && violation.video.includes(videoName.replace('.mp4', ''));
        });
        
        // Update UI
        document.getElementById('violationBadge').textContent = `${currentViolations.length} Violations`;
        document.getElementById('videoViolationsCount').textContent = currentViolations.length;
        
        // Display violations in table
        displayViolationsTable(currentViolations);
        
        // Update timeline
        timelineViolations = currentViolations;
        renderTimeline();
    } catch (error) {
        console.error('Error loading violations:', error);
        currentViolations = [];
    }
}

// Display violations in table
function displayViolationsTable(violations) {
    const tableBody = document.getElementById('violationsTable');
    tableBody.innerHTML = '';
    
    if (violations.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">
                    <i class="bi bi-check-circle"></i> No violations detected in this video
                </td>
            </tr>
        `;
        return;
    }
    
    violations.forEach(violation => {
        const row = document.createElement('tr');
        row.className = 'violation-item';
        row.onclick = () => seekToViolation(violation);
        
        // Extract time from timestamp
        const violationTime = violation.timestamp ? 
            formatTime(violation.timestamp) : 
            (violation.time ? new Date(violation.time).toLocaleTimeString() : 'N/A');
        
        // Confidence percentage
        const confidence = violation.confidence ? 
            `${(violation.confidence * 100).toFixed(1)}%` : 'N/A';
        
        row.innerHTML = `
            <td>
                <span class="badge bg-dark">${violationTime}</span>
            </td>
            <td>
                <span class="plate-display">${violation.plate || 'N/A'}</span>
            </td>
            <td>
                <span class="badge ${getViolationBadgeClass(violation.type)}">
                    ${violation.type || 'Unknown'}
                </span>
            </td>
            <td>
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar ${getConfidenceClass(violation.confidence)}" 
                         role="progressbar" 
                         style="width: ${violation.confidence ? violation.confidence * 100 : 0}%">
                        ${confidence}
                    </div>
                </div>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); viewViolationDetails('${violation.image}')">
                    <i class="bi bi-eye"></i> View
                </button>
                <button class="btn btn-sm btn-outline-success ms-1" onclick="event.stopPropagation(); seekToViolation(${JSON.stringify(violation).replace(/"/g, '&quot;')})">
                    <i class="bi bi-play-fill"></i> Jump
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Render timeline with violation markers
function renderTimeline() {
    const timeline = document.getElementById('videoTimeline');
    timeline.innerHTML = '';
    
    if (!player.duration || timelineViolations.length === 0) {
        timeline.innerHTML = '<div class="text-center text-muted p-3">No violations timeline available</div>';
        return;
    }
    
    const duration = player.duration;
    
    // Add current time indicator
    const indicator = document.createElement('div');
    indicator.className = 'current-time-indicator';
    indicator.id = 'currentTimeIndicator';
    timeline.appendChild(indicator);
    
    // Add violation markers
    timelineViolations.forEach(violation => {
        if (violation.timestamp) {
            const marker = document.createElement('div');
            marker.className = 'timeline-marker';
            marker.style.left = `${(violation.timestamp / duration) * 100}%`;
            marker.setAttribute('data-time', formatTime(violation.timestamp));
            marker.onclick = (e) => {
                e.stopPropagation();
                player.currentTime = violation.timestamp;
                highlightViolation(violation);
            };
            timeline.appendChild(marker);
        }
    });
    
    // Make timeline clickable
    timeline.onclick = (e) => {
        const rect = timeline.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percent = x / rect.width;
        player.currentTime = percent * duration;
    };
}

// Update current time indicator
function updateTimelineIndicator() {
    const indicator = document.getElementById('currentTimeIndicator');
    const timeline = document.getElementById('videoTimeline');
    
    if (indicator && timeline && player.duration) {
        const percent = (player.currentTime / player.duration) * 100;
        indicator.style.left = `${percent}%`;
    }
}

// Seek to violation time
function seekToViolation(violation) {
    if (violation.timestamp) {
        player.currentTime = violation.timestamp;
        player.play();
        highlightViolation(violation);
    }
}

// Highlight a violation in the table
function highlightViolation(violation) {
    document.querySelectorAll('.violation-item').forEach(row => {
        row.classList.remove('table-primary');
    });
}

// Update current time display
function updateCurrentTimeDisplay() {
    document.getElementById('currentTimeDisplay').textContent = formatTime(player.currentTime);
}

// Update duration display
function updateDurationDisplay() {
    document.getElementById('durationDisplay').textContent = formatTime(player.duration);
}

// Take snapshot from current video frame
function takeSnapshot() {
    const video = document.querySelector('video');
    const canvas = document.getElementById('snapshotCanvas');
    const context = canvas.getContext('2d');
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw current video frame
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Add timestamp overlay
    context.fillStyle = 'rgba(0, 0, 0, 0.7)';
    context.fillRect(10, canvas.height - 40, 300, 30);
    
    context.fillStyle = 'white';
    context.font = '14px Arial';
    context.fillText(`Time: ${formatTime(player.currentTime)}`, 20, canvas.height - 20);
    context.fillText(`Video: ${currentVideo}`, 20, canvas.height - 40);
    
    // Show modal
    document.getElementById('snapshotTime').textContent = 
        `Captured at ${formatTime(player.currentTime)} from ${currentVideo}`;
    
    const modal = new bootstrap.Modal(document.getElementById('snapshotModal'));
    modal.show();
}

// Download snapshot
function downloadSnapshot() {
    const canvas = document.getElementById('snapshotCanvas');
    const link = document.createElement('a');
    link.download = `snapshot_${currentVideo}_${formatTime(player.currentTime).replace(/:/g, '-')}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
}

// Save snapshot to evidence
function saveSnapshot() {
    // In production, send to backend API
    showNotification('Snapshot saved to evidence folder', 'success');
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('snapshotModal'));
    modal.hide();
}

// Download current video
function downloadVideo() {
    if (!currentVideo) {
        showNotification('No video selected', 'warning');
        return;
    }
    
    const link = document.createElement('a');
    link.href = `${API_EVIDENCE_VIDEOS}/${currentVideo}`;
    link.download = currentVideo;
    link.click();
}

// Load video metadata
async function loadVideoMetadata(videoName) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/video/metadata/${videoName}`);
        if (response.ok) {
            const metadata = await response.json();
            document.getElementById('videoSize').textContent = formatFileSize(metadata.size);
            document.getElementById('videoCreated').textContent = 
                new Date(metadata.created * 1000).toLocaleString();
        }
    } catch (error) {
        console.error('Error loading metadata:', error);
    }
}

// Update video statistics
function updateVideoStats(videos = []) {
    if (videos.length > 0) {
        document.getElementById('totalVideos').textContent = videos.length;
        
        // Calculate total size
        const totalSize = videos.reduce((sum, video) => sum + video.size, 0);
        document.getElementById('totalDuration').textContent = formatFileSize(totalSize);
        
        // Update violations count
        document.getElementById('totalViolationsInVideo').textContent = 
            timelineViolations.length;
    }
}

// Search videos
function searchVideos() {
    const searchTerm = document.getElementById('videoSearch').value.toLowerCase();
    const videoItems = document.querySelectorAll('.video-card');
    
    videoItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.parentElement.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
}

// View violation details
function viewViolationDetails(imageName) {
    if (imageName) {
        window.open(`${API_EVIDENCE_IMAGES}/${imageName}`, '_blank');
    } else {
        showNotification('No evidence image available', 'warning');
    }
}

// Utility functions
function formatTime(seconds) {
    if (!seconds) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getViolationBadgeClass(violationType) {
    if (!violationType) return 'bg-secondary';
    
    if (violationType.includes('Box Junction')) return 'bg-danger';
    if (violationType.includes('Red Light')) return 'bg-danger';
    if (violationType.includes('Speeding')) return 'bg-warning';
    if (violationType.includes('Illegal')) return 'bg-danger';
    
    return 'bg-primary';
}

function getConfidenceClass(confidence) {
    if (!confidence) return 'bg-secondary';
    
    if (confidence >= 0.9) return 'bg-success';
    if (confidence >= 0.7) return 'bg-info';
    if (confidence >= 0.5) return 'bg-warning';
    return 'bg-danger';
}

function updateAPIStatus(online) {
    const statusElement = document.getElementById('apiStatus');
    if (online) {
        statusElement.className = 'badge bg-success';
        statusElement.textContent = 'Online';
    } else {
        statusElement.className = 'badge bg-danger';
        statusElement.textContent = 'Offline';
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
    `;
    
    notification.innerHTML = `
        <i class="bi bi-${getNotificationIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 3000);
}

function getNotificationIcon(type) {
    switch(type) {
        case 'success': return 'check-circle';
        case 'warning': return 'exclamation-triangle';
        case 'danger': return 'x-circle';
        default: return 'info-circle';
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    
    switch(e.key) {
        case ' ':
            e.preventDefault();
            player.togglePlay();
            break;
        case 'ArrowLeft':
            e.preventDefault();
            player.currentTime -= 5;
            break;
        case 'ArrowRight':
            e.preventDefault();
            player.currentTime += 5;
            break;
        case 'f':
            if (e.ctrlKey) {
                e.preventDefault();
                player.fullscreen.toggle();
            }
            break;
        case 's':
            if (e.ctrlKey) {
                e.preventDefault();
                takeSnapshot();
            }
            break;
    }
});