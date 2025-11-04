// ========== Global Variables ==========
let historyChart = null;
let predictionChart = null;
let currentView = 'operator';
let bookingData = {
    selectedSpace: null,
    startTime: null,
    endTime: null,
    cost: 0
};

// ========== Initialize ==========
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupNavigation();
    setupBookingDatetime();
    loadOperatorDashboard();

    // Auto-refresh every 30 seconds for operator dashboard
    setInterval(() => {
        if (currentView === 'operator') {
            refreshParkingStatus();
        }
    }, 30000);
}

// ========== Navigation ==========
function setupNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');

    navButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const view = this.getAttribute('data-view');
            switchView(view);
        });
    });
}

function switchView(view) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-view') === view) {
            btn.classList.add('active');
        }
    });

    // Update view containers
    document.querySelectorAll('.view-container').forEach(container => {
        container.classList.add('hidden');
    });

    document.getElementById(`${view}-view`).classList.remove('hidden');
    currentView = view;

    // Load data for the view
    switch(view) {
        case 'operator':
            loadOperatorDashboard();
            break;
        case 'booking':
            // Booking wizard is initialized on demand
            break;
        case 'bookings':
            loadBookings();
            break;
    }
}

// ========== Operator Dashboard ==========
function loadOperatorDashboard() {
    updateParkingStatus();
    loadOccupancyHistory();
    loadOccupancyPrediction();
    loadRecentEvents();
    loadDailyStatistics();
}

async function updateParkingStatus() {
    try {
        const response = await fetch('/api/parking/status');
        const data = await response.json();

        if (data.success) {
            // Update statistics cards
            document.getElementById('availableSpaces').textContent = data.statistics.available;
            document.getElementById('occupiedSpaces').textContent = data.statistics.occupied;
            document.getElementById('totalSpaces').textContent = data.statistics.total;
            document.getElementById('occupancyRate').textContent = data.statistics.occupancy_rate + '%';

            // Update parking grid
            renderParkingGrid(data.spaces);

            // Update last update time
            updateLastUpdateTime(data.timestamp);
        }
    } catch (error) {
        console.error('Error updating parking status:', error);
        showToast('Failed to load parking status', 'error');
    }
}

function renderParkingGrid(spaces) {
    const grid = document.getElementById('parkingGrid');
    grid.innerHTML = '';

    spaces.forEach(space => {
        const spaceElement = document.createElement('div');
        spaceElement.className = `parking-space ${space.is_occupied ? 'occupied' : 'available'}`;
        spaceElement.innerHTML = `<div class="space-number">${space.space_number}</div>`;

        spaceElement.addEventListener('click', () => showSpaceDetails(space.space_number));

        grid.appendChild(spaceElement);
    });
}

async function showSpaceDetails(spaceNumber) {
    try {
        const response = await fetch(`/api/parking/space/${spaceNumber}`);
        const data = await response.json();

        if (data.success) {
            const modal = document.getElementById('spaceModal');
            const detailsContainer = document.getElementById('spaceDetails');

            detailsContainer.innerHTML = `
                <h3>Space ${data.space.space_number}</h3>
                <div class="space-detail-grid">
                    <div class="detail-item">
                        <strong>Status:</strong>
                        <span class="status-badge ${data.space.is_occupied ? 'occupied' : 'available'}">
                            ${data.space.is_occupied ? 'Occupied' : 'Available'}
                        </span>
                    </div>
                    <div class="detail-item">
                        <strong>Location:</strong> Row ${data.space.row + 1}, Column ${data.space.column + 1}
                    </div>
                    ${data.space.vehicle_type ? `
                        <div class="detail-item">
                            <strong>Vehicle Type:</strong> ${data.space.vehicle_type}
                        </div>
                    ` : ''}
                    ${data.space.last_updated ? `
                        <div class="detail-item">
                            <strong>Last Updated:</strong> ${formatDateTime(data.space.last_updated)}
                        </div>
                    ` : ''}
                </div>

                ${data.recent_events.length > 0 ? `
                    <h4 style="margin-top: 1.5rem; margin-bottom: 1rem;">Recent Activity</h4>
                    <div class="events-list">
                        ${data.recent_events.map(event => `
                            <div class="event-item">
                                <div class="event-info">
                                    <span class="event-type ${event.event_type}">${event.event_type}</span>
                                    <span class="event-time">${formatDateTime(event.timestamp)}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            `;

            modal.classList.add('show');
            modal.style.display = 'flex';
        }
    } catch (error) {
        console.error('Error loading space details:', error);
        showToast('Failed to load space details', 'error');
    }
}

function closeModal() {
    const modal = document.getElementById('spaceModal');
    modal.classList.remove('show');
    modal.style.display = 'none';
}

async function loadOccupancyHistory() {
    try {
        const response = await fetch('/api/occupancy/history?hours=24');
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            renderHistoryChart(data.data);
        }
    } catch (error) {
        console.error('Error loading occupancy history:', error);
    }
}

function renderHistoryChart(data) {
    const ctx = document.getElementById('historyChart');

    if (historyChart) {
        historyChart.destroy();
    }

    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => formatTime(d.timestamp)),
            datasets: [
                {
                    label: 'Occupied',
                    data: data.map(d => d.occupied),
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Available',
                    data: data.map(d => d.available),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

async function loadOccupancyPrediction() {
    try {
        const response = await fetch('/api/occupancy/predict?hours=6');
        const data = await response.json();

        if (data.success && data.predictions.length > 0) {
            renderPredictionChart(data.predictions);
        }
    } catch (error) {
        console.error('Error loading prediction:', error);
    }
}

function renderPredictionChart(data) {
    const ctx = document.getElementById('predictionChart');

    if (predictionChart) {
        predictionChart.destroy();
    }

    predictionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => formatTime(d.timestamp)),
            datasets: [{
                label: 'Predicted Occupancy Rate (%)',
                data: data.map(d => d.predicted_occupancy_rate * 100),
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

async function loadRecentEvents() {
    try {
        const response = await fetch('/api/events/recent?limit=20');
        const data = await response.json();

        if (data.success) {
            renderRecentEvents(data.events);
        }
    } catch (error) {
        console.error('Error loading events:', error);
    }
}

function renderRecentEvents(events) {
    const container = document.getElementById('recentEvents');

    if (events.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No recent events</p></div>';
        return;
    }

    container.innerHTML = events.map(event => `
        <div class="event-item">
            <div class="event-info">
                <span class="event-type ${event.event_type}">${event.event_type}</span>
                <span class="event-space">${event.space_number}</span>
                ${event.vehicle_type ? `<span class="event-vehicle">${event.vehicle_type}</span>` : ''}
            </div>
            <span class="event-time">${formatDateTime(event.timestamp)}</span>
        </div>
    `).join('');
}

async function loadDailyStatistics() {
    try {
        const response = await fetch('/api/statistics/summary');
        const data = await response.json();

        if (data.success) {
            document.getElementById('todayEntries').textContent = data.today.entries;
            document.getElementById('todayExits').textContent = data.today.exits;
            document.getElementById('todayAvgOccupancy').textContent = data.today.avg_occupancy_rate + '%';
            document.getElementById('todayPeakOccupancy').textContent = data.today.peak_occupancy;
        }
    } catch (error) {
        console.error('Error loading daily statistics:', error);
    }
}

function refreshParkingStatus() {
    updateParkingStatus();
    loadRecentEvents();
    showToast('Status refreshed', 'success');
}

// ========== Booking System ==========
function setupBookingDatetime() {
    const startTimeInput = document.getElementById('bookingStartTime');
    const endTimeInput = document.getElementById('bookingEndTime');

    // Set minimum to current time
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    startTimeInput.min = now.toISOString().slice(0, 16);

    // Default start time: 1 hour from now
    const defaultStart = new Date(Date.now() + 60 * 60 * 1000);
    defaultStart.setMinutes(defaultStart.getMinutes() - defaultStart.getTimezoneOffset());
    startTimeInput.value = defaultStart.toISOString().slice(0, 16);

    // Default end time: 3 hours from start
    const defaultEnd = new Date(defaultStart.getTime() + 3 * 60 * 60 * 1000);
    defaultEnd.setMinutes(defaultEnd.getMinutes() - defaultEnd.getTimezoneOffset());
    endTimeInput.value = defaultEnd.toISOString().slice(0, 16);

    // Update end time minimum when start time changes
    startTimeInput.addEventListener('change', function() {
        const startTime = new Date(this.value);
        const minEndTime = new Date(startTime.getTime() + 60 * 60 * 1000); // Minimum 1 hour
        minEndTime.setMinutes(minEndTime.getMinutes() - minEndTime.getTimezoneOffset());
        endTimeInput.min = minEndTime.toISOString().slice(0, 16);
    });
}

async function searchAvailableSpots() {
    const startTime = document.getElementById('bookingStartTime').value;
    const endTime = document.getElementById('bookingEndTime').value;

    if (!startTime || !endTime) {
        showToast('Please select start and end time', 'error');
        return;
    }

    const start = new Date(startTime);
    const end = new Date(endTime);

    if (end <= start) {
        showToast('End time must be after start time', 'error');
        return;
    }

    bookingData.startTime = startTime;
    bookingData.endTime = endTime;

    try {
        const response = await fetch(`/api/bookings/available?start_time=${startTime}&end_time=${endTime}`);
        const data = await response.json();

        if (data.success) {
            if (data.available_spaces.length === 0) {
                showToast('No spaces available for selected time', 'error');
                return;
            }

            renderAvailableSpaces(data.available_spaces);
            goToStep(2);
        } else {
            showToast(data.error || 'Failed to search available spaces', 'error');
        }
    } catch (error) {
        console.error('Error searching spaces:', error);
        showToast('Failed to search available spaces', 'error');
    }
}

function renderAvailableSpaces(spaces) {
    const container = document.getElementById('availableSpaces');

    container.innerHTML = spaces.map(space => `
        <div class="available-space-card" onclick="selectSpace('${space.space_number}', ${space.hourly_rate})">
            <div class="space-number">${space.space_number}</div>
            <div class="space-info">Row ${space.row + 1}, Column ${space.column + 1}</div>
            <div class="space-rate">$${space.hourly_rate}/hour</div>
        </div>
    `).join('');
}

async function selectSpace(spaceNumber, hourlyRate) {
    // Remove selection from all cards
    document.querySelectorAll('.available-space-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Select clicked card
    event.target.closest('.available-space-card').classList.add('selected');

    bookingData.selectedSpace = spaceNumber;

    // Calculate cost
    try {
        const response = await fetch('/api/bookings/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                space_number: spaceNumber,
                start_time: bookingData.startTime,
                end_time: bookingData.endTime
            })
        });

        const data = await response.json();

        if (data.success) {
            bookingData.cost = data.total_cost;
            bookingData.duration = data.duration_hours;

            // Show cost and proceed button
            showToast(`Space ${spaceNumber} selected - $${data.total_cost.toFixed(2)}`, 'success');

            // Add proceed button if not exists
            if (!document.querySelector('#proceed-to-details')) {
                const container = document.getElementById('availableSpaces');
                container.insertAdjacentHTML('afterend', `
                    <button id="proceed-to-details" class="btn btn-primary" onclick="goToStep(3)" style="margin-top: 1rem;">
                        Continue to Details
                    </button>
                `);
            }
        }
    } catch (error) {
        console.error('Error calculating cost:', error);
        showToast('Failed to calculate cost', 'error');
    }
}

function proceedToPayment() {
    // Validate form
    const name = document.getElementById('customerName').value.trim();
    const email = document.getElementById('customerEmail').value.trim();
    const vehicle = document.getElementById('vehicleNumber').value.trim();

    if (!name || !email || !vehicle) {
        showToast('Please fill in all required fields', 'error');
        return;
    }

    // Update summary
    document.getElementById('summarySpace').textContent = bookingData.selectedSpace;
    document.getElementById('summaryDuration').textContent = `${bookingData.duration.toFixed(2)} hours`;
    document.getElementById('summaryDate').textContent = formatDateTime(bookingData.startTime);
    document.getElementById('summaryTotal').textContent = `$${bookingData.cost.toFixed(2)}`;

    goToStep(4);
}

async function completeBooking() {
    const bookingDetails = {
        space_number: bookingData.selectedSpace,
        customer_name: document.getElementById('customerName').value.trim(),
        customer_email: document.getElementById('customerEmail').value.trim(),
        customer_phone: document.getElementById('customerPhone').value.trim(),
        vehicle_number: document.getElementById('vehicleNumber').value.trim(),
        vehicle_type: document.getElementById('vehicleType').value,
        start_time: bookingData.startTime,
        end_time: bookingData.endTime,
        notes: document.getElementById('bookingNotes').value.trim()
    };

    try {
        // Create booking
        const bookingResponse = await fetch('/api/bookings/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(bookingDetails)
        });

        const bookingData_result = await bookingResponse.json();

        if (!bookingData_result.success) {
            showToast(bookingData_result.error || 'Failed to create booking', 'error');
            return;
        }

        // Process payment
        const paymentResponse = await fetch('/api/payments/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                booking_reference: bookingData_result.booking.booking_reference,
                payment_method: document.getElementById('paymentMethod').value
            })
        });

        const paymentData = await paymentResponse.json();

        if (paymentData.success) {
            document.getElementById('bookingReference').textContent = bookingData_result.booking.booking_reference;
            goToStep(5);
            showToast('Booking completed successfully!', 'success');
        } else {
            showToast(paymentData.error || 'Payment failed', 'error');
        }
    } catch (error) {
        console.error('Error completing booking:', error);
        showToast('Failed to complete booking', 'error');
    }
}

function goToStep(stepNumber) {
    // Hide all steps
    document.querySelectorAll('.booking-step').forEach(step => {
        step.classList.add('hidden');
    });

    // Show selected step
    const stepMap = {
        1: 'step-time',
        2: 'step-space',
        3: 'step-details',
        4: 'step-payment',
        5: 'step-success'
    };

    document.getElementById(stepMap[stepNumber]).classList.remove('hidden');
}

function resetBookingForm() {
    // Reset booking data
    bookingData = {
        selectedSpace: null,
        startTime: null,
        endTime: null,
        cost: 0
    };

    // Reset form fields
    document.getElementById('customerName').value = '';
    document.getElementById('customerEmail').value = '';
    document.getElementById('customerPhone').value = '';
    document.getElementById('vehicleNumber').value = '';
    document.getElementById('bookingNotes').value = '';

    // Remove proceed button if exists
    const proceedBtn = document.querySelector('#proceed-to-details');
    if (proceedBtn) {
        proceedBtn.remove();
    }

    // Go to first step
    goToStep(1);

    // Reinitialize datetime
    setupBookingDatetime();
}

// ========== Bookings List ==========
async function loadBookings() {
    const status = document.getElementById('bookingStatusFilter').value;
    let url = '/api/bookings';
    if (status) {
        url += `?status=${status}`;
    }

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
            renderBookingsList(data.bookings);
        }
    } catch (error) {
        console.error('Error loading bookings:', error);
        showToast('Failed to load bookings', 'error');
    }
}

function renderBookingsList(bookings) {
    const container = document.getElementById('bookingsList');

    if (bookings.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No bookings found</h3>
                <p>There are no bookings matching your criteria</p>
            </div>
        `;
        return;
    }

    container.innerHTML = bookings.map(booking => `
        <div class="booking-card">
            <div class="booking-header">
                <div class="booking-reference-badge">${booking.booking_reference}</div>
                <span class="booking-status ${booking.status}">${booking.status}</span>
            </div>
            <div class="booking-details">
                <div class="booking-detail">
                    <div class="booking-detail-label">Space</div>
                    <div class="booking-detail-value">${booking.space_number}</div>
                </div>
                <div class="booking-detail">
                    <div class="booking-detail-label">Customer</div>
                    <div class="booking-detail-value">${booking.customer_name}</div>
                </div>
                <div class="booking-detail">
                    <div class="booking-detail-label">Vehicle</div>
                    <div class="booking-detail-value">${booking.vehicle_number}</div>
                </div>
                <div class="booking-detail">
                    <div class="booking-detail-label">Start Time</div>
                    <div class="booking-detail-value">${formatDateTime(booking.start_time)}</div>
                </div>
                <div class="booking-detail">
                    <div class="booking-detail-label">End Time</div>
                    <div class="booking-detail-value">${formatDateTime(booking.end_time)}</div>
                </div>
                <div class="booking-detail">
                    <div class="booking-detail-label">Amount</div>
                    <div class="booking-detail-value">$${booking.total_amount.toFixed(2)}</div>
                </div>
                <div class="booking-detail">
                    <div class="booking-detail-label">Payment Status</div>
                    <div class="booking-detail-value">
                        <span class="booking-status ${booking.payment_status}">${booking.payment_status}</span>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function filterBookings() {
    loadBookings();
}

// ========== Utility Functions ==========
function updateLastUpdateTime(timestamp) {
    const timeString = timestamp ? formatDateTime(timestamp) : new Date().toLocaleString();
    document.getElementById('lastUpdate').textContent = timeString;
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<div class="toast-message">${message}</div>`;

    container.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('spaceModal');
    if (event.target === modal) {
        closeModal();
    }
}
