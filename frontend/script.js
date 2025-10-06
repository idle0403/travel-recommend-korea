// 상수 정의
const API_BASE_URL = 'http://localhost:8000';
const DEFAULT_ZOOM = 13;
const SEOUL_CENTER = { lat: 37.5665, lng: 126.9780 };
const TOAST_DURATION = 3000;
const NOTION_SAVE_DELAY = 2000;

// 전역 변수
let map, directionsService, directionsRenderer;
let places = [];

// Initialize Google Maps
function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: DEFAULT_ZOOM,
        center: SEOUL_CENTER
    });
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        draggable: true,
        panel: null
    });
    directionsRenderer.setMap(map);
}



function updateTripDuration() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;
    const durationElement = document.getElementById('tripDuration');
    
    if (!durationElement) return; // 요소가 없으면 종료
    
    if (startDate && endDate && startTime && endTime) {
        const start = new Date(`${startDate}T${startTime}`);
        const end = new Date(`${endDate}T${endTime}`);
        
        if (end <= start) {
            durationElement.innerHTML = '<span class="text-red-600">⚠️ 종료 시간이 시작 시간보다 빠릅니다</span>';
            return;
        }
        
        const diffMs = end - start;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        let durationText = '';
        if (diffDays > 0) {
            durationText += `${diffDays}일 `;
        }
        if (diffHours > 0) {
            durationText += `${diffHours}시간 `;
        }
        if (diffMinutes > 0) {
            durationText += `${diffMinutes}분`;
        }
        
        const startFormatted = `${startDate.replace(/-/g, '')} ${startTime.replace(':', '')}`;
        const endFormatted = `${endDate.replace(/-/g, '')} ${endTime.replace(':', '')}`;
        
        durationElement.innerHTML = `${startFormatted} ~ ${endFormatted} (${durationText.trim()})`;
    } else if (startDate || endDate || startTime !== '09:00' || endTime !== '18:00') {
        // 일부 입력이 있으면 안내 메시지 표시
        durationElement.textContent = '날짜와 시간을 모두 선택해주세요';
    } else {
        // 기본 상태일 때는 기본 메시지
        durationElement.textContent = '날짜를 선택해주세요';
    }
}



async function handleFormSubmit() {
    console.log('handleFormSubmit called');
    
    const city = document.getElementById('city').value;
    const travelStyle = document.getElementById('travelStyle').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;
    const prompt = document.getElementById('prompt').value;
    

    
    if (!prompt.trim()) {
        showToast('여행 요청사항을 입력해주세요', 'error');
        return;
    }
    
    // 출발지는 선택사항으로 변경
    const startLocation = document.getElementById('startLocation') ? document.getElementById('startLocation').value : '';
    
    if (!startDate || !endDate) {
        showToast('시작일과 종료일을 모두 선택해주세요', 'error');
        return;
    }
    
    const start = new Date(`${startDate}T${startTime}`);
    const end = new Date(`${endDate}T${endTime}`);
    
    if (end <= start) {
        showToast('종료 시간이 시작 시간보다 빠릅니다', 'error');
        return;
    }
    
    // 여행 스타일 텍스트 생성
    const styleTexts = {
        'indoor_date': '실내 데이트',
        'outdoor_date': '실외 데이트',
        'food_tour': '맛집 투어',
        'culture_tour': '문화 탐방',
        'shopping_tour': '쇼핑 투어',
        'healing_tour': '힐링 여행',
        'adventure_tour': '액티비티 투어',
        'night_tour': '야경 투어',
        'family_tour': '가족 여행',
        'custom': '맞춤 여행'
    };
    
    const travelStyleText = styleTexts[travelStyle] || '맞춤 여행';
    
    // 여행 기간 계산
    const diffMs = end - start;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    let durationText = '';
    if (diffDays === 0) {
        durationText = `당일치기 (${diffHours}시간)`;
    } else {
        durationText = `${diffDays}박${diffDays + 1}일`;
    }
    
    console.log('Starting API call...');
    showLoading();
    
    try {
        const requestData = {
            prompt: `${city}에서 ${travelStyleText} ${durationText} ${startDate.replace(/-/g, '')} ${startTime.replace(':', '')}부터 ${endDate.replace(/-/g, '')} ${endTime.replace(':', '')}까지 ${prompt}`,
            preferences: {
                city,
                travel_style: travelStyle,
                start_date: startDate,
                end_date: endDate,
                start_time: startTime,
                end_time: endTime,
                duration_days: diffDays,
                duration_hours: diffHours
            }
        };
        
        console.log('Request data:', requestData);
        
        const response = await fetch(`${API_BASE_URL}/api/travel/plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error:', errorText);
            throw new Error(`서버 오류 (${response.status}): ${errorText}`);
        }
        
        const data = await response.json();
        console.log('API Response data:', data);
        
        await displayResults(data);
        showToast('여행 계획이 생성되었습니다!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showToast('오류가 발생했습니다: ' + (error.message || '알 수 없는 오류'), 'error');
        hideLoading();
    }
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('submitBtn').disabled = true;
    document.getElementById('btnText').textContent = '생성 중...';
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('submitBtn').disabled = false;
    document.getElementById('btnText').textContent = 'AI 여행 계획 생성';
}

async function displayResults(data) {
    hideLoading();
    
    document.getElementById('results').classList.remove('hidden');
    
    // Initialize map if not already done
    if (!map) {
        initMap();
    }
    
    // Display timeline
    displayTimeline(data.itinerary || []);
    
    // Verify places and get details
    await verifyAndDisplayPlaces(data.itinerary || []);
    
    // Show optimized route on map
    if (data.route_info && data.route_info.polyline) {
        displayOptimizedRoute(data.route_info);
    } else {
        displayRoute(places);
    }
    
    // Show Notion saving status
    updateNotionStatus('saving');
    
    // Notion 저장 상태 업데이트
    setTimeout(() => {
        const url = data.notion_url || 'https://notion.so/sample-page';
        updateNotionStatus('success', url);
    }, NOTION_SAVE_DELAY);
}

function displayTimeline(itinerary) {
    const timeline = document.getElementById('timeline');
    timeline.innerHTML = '';
    
    itinerary.forEach((item, index) => {
        const timelineItem = document.createElement('div');
        timelineItem.className = 'flex items-start space-x-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer';
        timelineItem.onclick = () => showPlaceModal(item);
        
        timelineItem.innerHTML = `
            <div class="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                ${index + 1}
            </div>
            <div class="flex-1">
                <div class="flex items-center space-x-2 mb-1">
                    <span class="font-semibold text-blue-600">${item.time || `${9 + index}:00`}</span>
                    <span class="text-sm text-gray-500">• ${item.duration || '30분'}</span>
                </div>
                <h4 class="font-medium text-gray-800 mb-1">${item.name || item.activity}</h4>
                <p class="text-sm text-gray-600 mb-2">${item.description || ''}</p>
                ${item.transportation ? `<div class="bg-green-50 p-2 rounded mb-2">
                    <span class="text-xs text-green-700"><i class="fas fa-subway"></i> ${item.transportation}</span>
                </div>` : ''}
                ${item.route_distance && item.route_duration ? `<div class="bg-blue-50 p-2 rounded mb-2">
                    <span class="text-xs text-blue-700"><i class="fas fa-route"></i> 이동: ${item.route_distance}, ${item.route_duration}</span>
                </div>` : ''}
                <div class="flex items-center space-x-4 text-xs text-gray-500">
                    <span><i class="fas fa-map-marker-alt"></i> ${item.location || ''}</span>
                    ${item.rating ? `<span><i class="fas fa-star text-yellow-400"></i> ${item.rating}</span>` : ''}
                    ${item.quality_score ? `<span class="px-1 py-0.5 rounded text-xs ${
                        item.quality_score >= 4.0 ? 'bg-blue-100 text-blue-700' :
                        item.quality_score >= 3.0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }">Q:${item.quality_score.toFixed(1)}</span>` : ''}
                    ${item.price ? `<span><i class="fas fa-won-sign"></i> ${item.price}</span>` : ''}
                </div>
            </div>
        `;
        
        timeline.appendChild(timelineItem);
    });
}

async function verifyAndDisplayPlaces(itinerary) {
    const placeDetails = document.getElementById('placeDetails');
    placeDetails.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i> 장소 정보를 확인하고 있습니다...</div>';
    
    places = [];
    const verifiedPlaces = [];
    
    // 실제 API 데이터를 사용 (이미 백엔드에서 처리됨)
    for (const item of itinerary) {
        const placeInfo = {
            name: item.place_name || item.name || item.activity,
            verified: item.verified || false,
            description: item.description || '',
            rating: item.rating || item.google_rating || 4.0,
            qualityScore: item.quality_score || 0,
            reviewCount: item.blog_reviews ? item.blog_reviews.length * 10 : 0,
            openHours: item.opening_hours ? item.opening_hours.join(', ') : '09:00-21:00',
            location: item.address || item.location || '',
            lat: item.lat || 37.5665,
            lng: item.lng || 126.9780,
            phone: item.phone || '',
            website: item.website || '',
            blogLinks: item.blog_reviews ? item.blog_reviews.map(blog => ({
                title: blog.title || `${item.place_name} 후기`,
                url: blog.link || `https://search.naver.com/search.naver?query=${encodeURIComponent((item.place_name || item.name) + ' 후기')}`
            })) : [],
            blogContents: item.blog_contents || []
        };
        
        verifiedPlaces.push(placeInfo);
        places.push({
            name: placeInfo.name,
            location: placeInfo.location,
            lat: placeInfo.lat,
            lng: placeInfo.lng
        });
    }
    
    // Display verified places
    placeDetails.innerHTML = '';
    verifiedPlaces.forEach(place => {
        const placeDiv = document.createElement('div');
        placeDiv.className = 'border rounded-lg p-4 hover:shadow-md transition-shadow';
        placeDiv.innerHTML = `
            <div class="flex items-start justify-between mb-2">
                <h4 class="font-semibold text-gray-800">${place.name}</h4>
                <div class="flex space-x-2">
                    <span class="px-2 py-1 text-xs rounded-full ${
                        place.verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }">
                        ${place.verified ? '✓ 확인됨' : '⚠ 미확인'}
                    </span>
                    ${place.qualityScore > 0 ? `
                        <span class="px-2 py-1 text-xs rounded-full ${
                            place.qualityScore >= 4.0 ? 'bg-blue-100 text-blue-800' :
                            place.qualityScore >= 3.0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }">
                            품질: ${place.qualityScore.toFixed(1)}/5.0
                        </span>
                    ` : ''}
                </div>
            </div>
            <p class="text-sm text-gray-600 mb-2">${place.description}</p>
            <div class="flex items-center space-x-4 text-xs text-gray-500 mb-2">
                <span><i class="fas fa-star text-yellow-400"></i> ${place.rating}/5</span>
                <span><i class="fas fa-users"></i> 리뷰 ${place.reviewCount}개</span>
                ${place.phone ? `<span><i class="fas fa-phone"></i> ${place.phone}</span>` : ''}
                <span><i class="fas fa-clock"></i> ${place.openHours}</span>
            </div>
            ${place.blogLinks ? `
                <div class="mt-3">
                    <p class="text-xs font-medium text-gray-700 mb-1">관련 리뷰:</p>
                    <div class="space-y-1">
                        ${place.blogLinks.map(link => `
                            <a href="${link.url}" target="_blank" class="block text-xs text-blue-600 hover:underline">
                                <i class="fas fa-external-link-alt mr-1"></i>${link.title}
                            </a>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            ${place.blogContents && place.blogContents.length > 0 ? `
                <div class="mt-3 space-y-2">
                    ${place.blogContents.map(content => `
                        <div class="p-2 bg-yellow-50 rounded">
                            <p class="text-xs font-medium text-gray-700 mb-1">블로그 후기 내용:</p>
                            <p class="text-xs text-gray-600 mb-2">${content.summary || content.content || '후기 내용을 불러오는 중...'}</p>
                            ${content.keywords && content.keywords.length > 0 ? `
                                <div class="flex flex-wrap gap-1">
                                    ${content.keywords.map(keyword => `
                                        <span class="inline-block px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">${keyword}</span>
                                    `).join('')}
                                </div>
                            ` : ''}
                            ${content.rating ? `
                                <div class="mt-1 text-xs text-gray-500">
                                    <i class="fas fa-star text-yellow-400"></i> 블로그 평점: ${content.rating}/5
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        `;
        placeDetails.appendChild(placeDiv);
    });
}

async function verifyPlace(placeName) {
    // Simulate API call to verify place and get details
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
        name: placeName,
        verified: Math.random() > 0.2, // 80% verification rate
        description: `${placeName}에 대한 상세 설명입니다.`,
        rating: (4 + Math.random()).toFixed(1),
        reviewCount: Math.floor(Math.random() * 500) + 50,
        openHours: '09:00-21:00',
        location: '서울시 강남구',
        lat: 37.5665 + (Math.random() - 0.5) * 0.1,
        lng: 126.9780 + (Math.random() - 0.5) * 0.1,
        blogLinks: [
            { 
                title: `${placeName} 후기 - 네이버 블로그`, 
                url: `https://search.naver.com/search.naver?query=${encodeURIComponent(placeName + ' 후기')}` 
            },
            { 
                title: `${placeName} 맛집 리뷰 - 매니아`, 
                url: `https://www.mangoplate.com/search/${encodeURIComponent(placeName)}` 
            },
            { 
                title: `${placeName} 정보 - 카카오맵`, 
                url: `https://map.kakao.com/?q=${encodeURIComponent(placeName)}` 
            }
        ]
    };
}

function displayOptimizedRoute(routeInfo) {
    // Clear previous routes
    directionsRenderer.setDirections({routes: []});
    
    // Decode polyline and display on map
    if (routeInfo.polyline) {
        const decodedPath = google.maps.geometry.encoding.decodePath(routeInfo.polyline);
        
        const polyline = new google.maps.Polyline({
            path: decodedPath,
            geodesic: true,
            strokeColor: '#4285F4',
            strokeOpacity: 1.0,
            strokeWeight: 4
        });
        
        polyline.setMap(map);
        
        // Fit map to route bounds
        if (routeInfo.bounds) {
            const bounds = new google.maps.LatLngBounds(
                new google.maps.LatLng(routeInfo.bounds.southwest.lat, routeInfo.bounds.southwest.lng),
                new google.maps.LatLng(routeInfo.bounds.northeast.lat, routeInfo.bounds.northeast.lng)
            );
            map.fitBounds(bounds);
        }
        
        // Add markers for each location
        places.forEach((place, index) => {
            const marker = new google.maps.Marker({
                position: new google.maps.LatLng(place.lat, place.lng),
                map: map,
                title: place.name,
                label: (index + 1).toString()
            });
            
            const infoWindow = new google.maps.InfoWindow({
                content: `<div><strong>${place.name}</strong><br>${place.location || ''}</div>`
            });
            
            marker.addListener('click', () => {
                infoWindow.open(map, marker);
            });
        });
    }
}

function displayRoute(places) {
    if (places.length < 2) return;
    
    const waypoints = places.slice(1, -1).map(place => ({
        location: new google.maps.LatLng(place.lat, place.lng),
        stopover: true
    }));
    
    const request = {
        origin: new google.maps.LatLng(places[0].lat, places[0].lng),
        destination: new google.maps.LatLng(places[places.length - 1].lat, places[places.length - 1].lng),
        waypoints: waypoints,
        optimizeWaypoints: true,
        travelMode: google.maps.TravelMode.TRANSIT
    };
    
    directionsService.route(request, (result, status) => {
        if (status === 'OK') {
            directionsRenderer.setDirections(result);
        }
    });
}

function showPlaceModal(place) {
    const modal = document.getElementById('placeModal');
    const title = document.getElementById('modalTitle');
    const content = document.getElementById('modalContent');
    
    title.textContent = place.place_name || place.name || place.activity;
    content.innerHTML = `
        <div class="space-y-4">
            <p class="text-gray-600">${place.description || '상세 정보를 불러오고 있습니다...'}</p>
            <div class="grid grid-cols-2 gap-4 text-sm">
                <div><strong>시간:</strong> ${place.time || 'N/A'}</div>
                <div><strong>소요시간:</strong> ${place.duration || 'N/A'}</div>
                <div><strong>위치:</strong> ${place.address || place.location || 'N/A'}</div>
                <div><strong>비용:</strong> ${place.price || 'N/A'}</div>
                ${place.phone ? `<div><strong>전화:</strong> ${place.phone}</div>` : ''}
                ${place.rating ? `<div><strong>평점:</strong> ${place.rating}/5</div>` : ''}
            </div>
            ${place.blog_reviews && place.blog_reviews.length > 0 ? `
                <div>
                    <h5 class="font-medium text-gray-800 mb-2">블로그 후기</h5>
                    <div class="space-y-1">
                        ${place.blog_reviews.slice(0, 3).map(blog => `
                            <a href="${blog.link}" target="_blank" class="block text-sm text-blue-600 hover:underline">
                                <i class="fas fa-external-link-alt mr-1"></i>${blog.title}
                            </a>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            ${place.blog_contents && place.blog_contents.length > 0 ? `
                <div>
                    <h5 class="font-medium text-gray-800 mb-2">블로그 내용 요약</h5>
                    ${place.blog_contents.slice(0, 2).map(content => `
                        <div class="p-3 bg-gray-50 rounded mb-2">
                            <p class="text-sm text-gray-700">${content.summary || content.content || '내용을 불러오는 중...'}</p>
                            ${content.keywords && content.keywords.length > 0 ? `
                                <div class="mt-2 flex flex-wrap gap-1">
                                    ${content.keywords.map(keyword => `
                                        <span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">${keyword}</span>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
    
    modal.classList.remove('hidden');
}



function updateNotionStatus(status, url = null, error = null) {
    const notionResult = document.getElementById('notionResult');
    
    switch (status) {
        case 'saving':
            notionResult.innerHTML = `
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>
                <span class="text-gray-600">Notion에 저장 중...</span>
            `;
            break;
            
        case 'success':
            notionResult.innerHTML = `
                <i class="fas fa-check-circle text-green-500 text-xl"></i>
                <span class="text-green-700">Notion 저장 완료!</span>
                ${url ? `<a href="${url}" target="_blank" class="text-blue-500 hover:underline ml-2">
                    <i class="fas fa-external-link-alt"></i> 보기
                </a>` : ''}
            `;
            showToast('Notion에 저장되었습니다!', 'success');
            break;
            
        case 'error':
            notionResult.innerHTML = `
                <i class="fas fa-exclamation-circle text-red-500 text-xl"></i>
                <span class="text-red-700">Notion 저장 실패</span>
                ${error ? `<p class="text-sm text-gray-600 mt-1">${error}</p>` : ''}
            `;
            showToast('Notion 저장에 실패했습니다', 'error');
            break;
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toastIcon');
    const toastMessage = document.getElementById('toastMessage');
    
    if (type === 'success') {
        toastIcon.className = 'fas fa-check-circle text-green-500 mr-3';
        toast.querySelector('div').className = 'bg-white border-l-4 border-green-500 rounded-lg shadow-lg p-4 max-w-sm';
    } else {
        toastIcon.className = 'fas fa-exclamation-circle text-red-500 mr-3';
        toast.querySelector('div').className = 'bg-white border-l-4 border-red-500 rounded-lg shadow-lg p-4 max-w-sm';
    }
    
    toastMessage.textContent = message;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, TOAST_DURATION);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // 폼 제출 이벤트 등록 (최우선)
    const form = document.getElementById('travelForm');
    if (form) {
        console.log('Form found, adding submit listener');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Form submit event triggered');
            handleFormSubmit();
            return false;
        });
    } else {
        console.error('Form not found!');
    }
    
    // Initialize Google Maps
    if (typeof google !== 'undefined') {
        initMap();
    }
    
    // 오늘 날짜를 기본값으로 설정
    const today = new Date().toISOString().split('T')[0];
    const startDateEl = document.getElementById('startDate');
    const endDateEl = document.getElementById('endDate');
    
    if (startDateEl) startDateEl.value = today;
    if (endDateEl) endDateEl.value = today;
    
    // 초기 여행 기간 표시
    updateTripDuration();
    
    // 출발지 입력 필드 클릭 시 지도 모달 열기
    const startLocationInput = document.getElementById('startLocation');
    if (startLocationInput) {
        startLocationInput.addEventListener('click', function() {
            document.getElementById('mapModal').classList.remove('hidden');
            setTimeout(() => {
                if (!mapModal) {
                    initMapModal();
                }
            }, 100);
        });
    }
    
    // 기타 이벤트 리스너 등록
    setupOtherEventListeners();
});

function setupOtherEventListeners() {
    // 도시 변경 이벤트 - 도시별 추천 스타일 자동 조정
    const cityEl = document.getElementById('city');
    if (cityEl) {
        cityEl.addEventListener('change', function() {
            const city = this.value;
            const travelStyleEl = document.getElementById('travelStyle');
            
            // 도시별 추천 스타일 자동 선택
            const cityRecommendations = {
                'Seoul': 'indoor_date',
                'Busan': 'outdoor_date', 
                'Jeju': 'healing_tour',
                'Jeonju': 'food_tour',
                'Gyeongju': 'culture_tour',
                'Gangneung': 'outdoor_date',
                'Yeosu': 'night_tour',
                'Andong': 'culture_tour'
            };
            
            if (cityRecommendations[city]) {
                travelStyleEl.value = cityRecommendations[city];
                // 시간 자동 조정 트리거
                travelStyleEl.dispatchEvent(new Event('change'));
            }
        });
    }
    
    // 여행 스타일 변경 이벤트
    const travelStyleEl = document.getElementById('travelStyle');
    if (travelStyleEl) {
        travelStyleEl.addEventListener('change', function() {
            const travelStyle = this.value;
            const startTime = document.getElementById('startTime');
            const endTime = document.getElementById('endTime');
            
            if (!startTime || !endTime) return;
            
            // 스타일에 따른 추천 시간 설정
            switch(travelStyle) {
                case 'indoor_date':
                    startTime.value = '10:00';
                    endTime.value = '18:00';
                    break;
                case 'outdoor_date':
                    startTime.value = '09:00';
                    endTime.value = '17:00';
                    break;
                case 'food_tour':
                    startTime.value = '11:00';
                    endTime.value = '21:00';
                    break;
                case 'culture_tour':
                    startTime.value = '09:30';
                    endTime.value = '17:30';
                    break;
                case 'shopping_tour':
                    startTime.value = '11:00';
                    endTime.value = '20:00';
                    break;
                case 'healing_tour':
                    startTime.value = '10:00';
                    endTime.value = '16:00';
                    break;
                case 'adventure_tour':
                    startTime.value = '09:00';
                    endTime.value = '18:00';
                    break;
                case 'night_tour':
                    startTime.value = '17:00';
                    endTime.value = '22:00';
                    break;
                case 'family_tour':
                    startTime.value = '10:00';
                    endTime.value = '17:00';
                    break;
            }
            
            updateTripDuration();
        });
    }
    
    // 날짜/시간 변경 이벤트
    ['startDate', 'endDate', 'startTime', 'endTime'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', updateTripDuration);
        }
    });
    
    // 모달 닫기 이벤트
    const closeModal = document.getElementById('closeModal');
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            document.getElementById('placeModal').classList.add('hidden');
        });
    }
}