// 상수 정의
const API_BASE_URL = window.location.origin;
const DEFAULT_ZOOM = 13;
const SEOUL_CENTER = { lat: 37.5665, lng: 126.9780 };
const TOAST_DURATION = 3000;
const NOTION_SAVE_DELAY = 2000;

// 전역 변수
let map, directionsService, directionsRenderer;
let places = [];

// Initialize Google Maps
function initMap() {
    console.log('Initializing Google Maps...');
    
    const mapElement = document.getElementById('map');
    if (!mapElement) {
        console.error('Map element not found');
        return;
    }
    
    if (typeof google === 'undefined' || !google.maps) {
        console.error('Google Maps API not loaded');
        return;
    }
    
    try {
        // 도시별 지도 중심점 설정
        const cityCenter = getCityCenter();
        
        map = new google.maps.Map(mapElement, {
            zoom: DEFAULT_ZOOM,
            center: cityCenter,
            mapTypeControl: true,
            streetViewControl: true,
            fullscreenControl: true,
            zoomControl: true
        });
        
        directionsService = new google.maps.DirectionsService();
        directionsRenderer = new google.maps.DirectionsRenderer({
            draggable: false,
            panel: null,
            suppressMarkers: false
        });
        directionsRenderer.setMap(map);
        
        console.log('Google Maps initialized successfully');
        
        // 지도 로드 완료 이벤트
        google.maps.event.addListenerOnce(map, 'tilesloaded', function() {
            console.log('Map tiles loaded');
        });
        
    } catch (error) {
        console.error('Error initializing Google Maps:', error);
    }
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
            prompt: `${city}에서 ${travelStyleText} ${durationText} ${startDate.replace(/-/g, '')} ${startTime.replace(':', '')}부터 ${endDate.replace(/-/g, '')} ${endTime.replace(':', '')}까지 ${startLocation ? `출발지: ${startLocation}에서 시작하여 ` : ''}${prompt}`,
            preferences: {
                city,
                travel_style: travelStyle,
                start_date: startDate,
                end_date: endDate,
                start_time: startTime,
                end_time: endTime,
                start_location: startLocation,
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

// 전역 변수
let currentDay = 1;
let dayGroups = {};

function displayTimeline(itinerary) {
    // 일자별 데이터 그룹화
    dayGroups = groupByDay(itinerary);
    
    // 탭 생성
    createDayTabs(dayGroups);
    
    // 첫 번째 날 표시
    displayDayTimeline(currentDay);
}

function groupByDay(itinerary) {
    const groups = {};
    
    // 일정이 없으면 빈 객체 반환
    if (!itinerary || itinerary.length === 0) {
        return { 1: [] };
    }
    
    itinerary.forEach((item, index) => {
        // day 필드가 있으면 사용, 없으면 시간 기준으로 일자 계산
        let day = item.day;
        
        if (!day) {
            // 시간 기준으로 일자 추정 (09:00부터 시작해서 24시간 넘어가면 다음날)
            const timeStr = item.time || '09:00';
            const hour = parseInt(timeStr.split(':')[0]);
            
            // 첫 번째 아이템이거나 시간이 이전보다 작으면서 새벽 시간대면 다음날
            if (index === 0) {
                day = 1;
            } else {
                const prevItem = itinerary[index - 1];
                const prevHour = parseInt((prevItem.time || '09:00').split(':')[0]);
                
                if (hour < prevHour && hour < 12) {
                    // 이전 아이템의 day를 찾아서 +1
                    const prevDay = prevItem.calculatedDay || prevItem.day || 1;
                    day = prevDay + 1;
                } else {
                    // 같은 날
                    const prevDay = prevItem.calculatedDay || prevItem.day || 1;
                    day = prevDay;
                }
            }
            
            // 계산된 day를 아이템에 저장
            item.calculatedDay = day;
        }
        
        if (!groups[day]) {
            groups[day] = [];
        }
        groups[day].push({...item, day: day});
    });
    
    // 빈 그룹이 있으면 제거
    Object.keys(groups).forEach(key => {
        if (groups[key].length === 0) {
            delete groups[key];
        }
    });
    
    console.log('Grouped itinerary by day:', groups);
    return groups;
}

function createDayTabs(dayGroups) {
    const tabsContainer = document.getElementById('dayTabs');
    const dayCount = Object.keys(dayGroups).length;
    
    console.log('Creating day tabs for', dayCount, 'days');
    
    if (dayCount <= 1) {
        tabsContainer.classList.add('hidden');
        console.log('Only one day, hiding tabs');
        return;
    }
    
    tabsContainer.classList.remove('hidden');
    tabsContainer.innerHTML = '';
    
    // 일자 순서대로 정렬
    const sortedDays = Object.keys(dayGroups).sort((a, b) => parseInt(a) - parseInt(b));
    
    sortedDays.forEach(day => {
        const dayNum = parseInt(day);
        const dayData = dayGroups[day];
        
        const tab = document.createElement('button');
        tab.className = `px-4 py-2 mr-2 mb-2 rounded-lg font-medium transition-colors ${
            dayNum === currentDay ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-blue-100'
        }`;
        tab.textContent = `${dayNum}일차 (${dayData.length}개)`;
        tab.setAttribute('data-day', dayNum);
        
        tab.onclick = () => {
            console.log(`Tab clicked: Day ${dayNum}`);
            currentDay = dayNum;
            displayDayTimeline(currentDay);
            updateTabStyles();
        };
        
        tabsContainer.appendChild(tab);
    });
    
    console.log('Created tabs for days:', sortedDays);
}

function updateTabStyles() {
    const tabs = document.querySelectorAll('#dayTabs button');
    tabs.forEach(tab => {
        const tabDay = parseInt(tab.getAttribute('data-day'));
        if (tabDay === currentDay) {
            tab.className = 'px-4 py-2 mr-2 mb-2 rounded-lg font-medium bg-blue-500 text-white transition-colors';
        } else {
            tab.className = 'px-4 py-2 mr-2 mb-2 rounded-lg font-medium bg-gray-100 text-gray-700 hover:bg-blue-100 transition-colors';
        }
    });
    
    console.log(`Updated tab styles, current day: ${currentDay}`);
}

function displayDayTimeline(day) {
    const timeline = document.getElementById('timeline');
    const dayData = dayGroups[day] || [];
    
    console.log(`Displaying timeline for day ${day}:`, dayData);
    
    timeline.innerHTML = '';
    
    if (dayData.length === 0) {
        timeline.innerHTML = '<div class="text-center py-8 text-gray-500">이 날의 일정이 없습니다.</div>';
        return;
    }
    
    dayData.forEach((item, index) => {
        const timelineItem = document.createElement('div');
        timelineItem.className = 'flex items-start space-x-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer';
        timelineItem.onclick = () => showPlaceModal(item);
        
        const placeName = item.place_name || item.name || item.activity || '장소명 없음';
        const time = item.time || `${9 + index}:00`;
        const duration = item.duration || '30분';
        const description = item.description || '';
        const location = item.address || item.location || '';
        
        timelineItem.innerHTML = `
            <div class="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                ${index + 1}
            </div>
            <div class="flex-1">
                <div class="flex items-center space-x-2 mb-1">
                    <span class="font-semibold text-blue-600">${time}</span>
                    <span class="text-sm text-gray-500">• ${duration}</span>
                    <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">${day}일차</span>
                </div>
                <h4 class="font-medium text-gray-800 mb-1">${placeName}</h4>
                <p class="text-sm text-gray-600 mb-2">${description}</p>
                ${item.transportation ? `<div class="bg-green-50 p-2 rounded mb-2">
                    <span class="text-xs text-green-700"><i class="fas fa-subway"></i> ${item.transportation}</span>
                </div>` : ''}
                ${item.route_distance && item.route_duration ? `<div class="bg-blue-50 p-2 rounded mb-2">
                    <span class="text-xs text-blue-700"><i class="fas fa-route"></i> 이동: ${item.route_distance}, ${item.route_duration}</span>
                </div>` : ''}
                <div class="flex items-center space-x-4 text-xs text-gray-500">
                    <span><i class="fas fa-map-marker-alt"></i> ${location}</span>
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
    
    // 지도에 해당 날짜 데이터만 표시
    updateMapForDay(dayData);
    
    // 장소 상세정보도 업데이트
    verifyAndDisplayPlaces(dayData);
    
    console.log(`Timeline displayed for day ${day} with ${dayData.length} items`);
}

function updateMapForDay(dayData) {
    if (!map || !dayData || dayData.length === 0) return;
    
    // 기존 마커 제거
    if (window.currentMarkers) {
        window.currentMarkers.forEach(marker => marker.setMap(null));
    }
    window.currentMarkers = [];
    
    const bounds = new google.maps.LatLngBounds();
    
    dayData.forEach((item, index) => {
        const lat = item.lat || 37.5665;
        const lng = item.lng || 126.9780;
        const position = new google.maps.LatLng(lat, lng);
        
        const marker = new google.maps.Marker({
            position: position,
            map: map,
            title: item.place_name || item.name || item.activity,
            label: (index + 1).toString(),
            icon: {
                url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                scaledSize: new google.maps.Size(32, 32)
            }
        });
        
        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div style="max-width: 250px;">
                    <h4 style="margin: 0 0 8px 0; font-weight: bold; color: #1a73e8;">${item.place_name || item.name || item.activity}</h4>
                    <p style="margin: 0 0 4px 0; font-size: 13px; color: #333;">${item.description || ''}</p>
                    <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">
                        <i class="fas fa-map-marker-alt" style="color: #ea4335;"></i> ${item.address || item.location || ''}
                    </p>
                    ${item.time ? `<p style="margin: 0; font-size: 11px; color: #888;">
                        <i class="fas fa-clock"></i> ${item.time} (${item.duration || '30분'})
                    </p>` : ''}
                </div>
            `
        });
        
        marker.addListener('click', () => {
            if (window.currentInfoWindow) {
                window.currentInfoWindow.close();
            }
            infoWindow.open(map, marker);
            window.currentInfoWindow = infoWindow;
        });
        
        window.currentMarkers.push(marker);
        bounds.extend(position);
    });
    
    if (dayData.length > 0) {
        map.fitBounds(bounds);
        
        google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
            if (map.getZoom() > 15) {
                map.setZoom(15);
            }
        });
    }
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
    console.log('displayOptimizedRoute called with:', routeInfo);
    
    if (!map) {
        console.error('Map not initialized');
        return;
    }
    
    // Clear previous routes and markers
    if (directionsRenderer) {
        directionsRenderer.setDirections({routes: []});
    }
    
    if (window.currentMarkers) {
        window.currentMarkers.forEach(marker => marker.setMap(null));
    }
    window.currentMarkers = [];
    
    // 8단계 아키텍처에서 받은 경로 정보 처리
    const locations = routeInfo.locations || places;
    
    if (!locations || locations.length === 0) {
        console.log('No locations to display');
        return;
    }
    
    console.log('Displaying optimized route with locations:', locations);
    
    // 경로 라인 표시 (polyline이 있는 경우)
    if (routeInfo.polyline && routeInfo.polyline !== "sample_encoded_polyline_string") {
        try {
            let pathCoords = [];
            
            // 커스텀 polyline 형식 처리 ("lat,lng|lat,lng" 형태)
            if (routeInfo.polyline.includes('|')) {
                pathCoords = routeInfo.polyline.split('|').map(coord => {
                    const [lat, lng] = coord.split(',').map(Number);
                    return new google.maps.LatLng(lat, lng);
                });
            } else {
                // Google 표준 polyline 디코딩
                pathCoords = google.maps.geometry.encoding.decodePath(routeInfo.polyline);
            }
            
            const routeLine = new google.maps.Polyline({
                path: pathCoords,
                geodesic: true,
                strokeColor: '#4285F4',
                strokeOpacity: 0.8,
                strokeWeight: 4
            });
            
            routeLine.setMap(map);
            console.log('Route polyline displayed');
        } catch (error) {
            console.error('Error displaying polyline:', error);
        }
    }
    
    // 마커 표시
    const bounds = new google.maps.LatLngBounds();
    
    locations.forEach((location, index) => {
        const lat = location.lat || 37.5665;
        const lng = location.lng || 126.9780;
        const position = new google.maps.LatLng(lat, lng);
        
        const marker = new google.maps.Marker({
            position: position,
            map: map,
            title: location.name,
            label: (index + 1).toString(),
            icon: {
                url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
                scaledSize: new google.maps.Size(32, 32)
            }
        });
        
        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div style="max-width: 250px;">
                    <h4 style="margin: 0 0 8px 0; font-weight: bold; color: #1a73e8;">${location.name}</h4>
                    <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">${location.location || ''}</p>
                    <p style="margin: 0; font-size: 11px; color: #888;">8단계 최적화된 경로</p>
                </div>
            `
        });
        
        marker.addListener('click', () => {
            if (window.currentInfoWindow) {
                window.currentInfoWindow.close();
            }
            infoWindow.open(map, marker);
            window.currentInfoWindow = infoWindow;
        });
        
        window.currentMarkers.push(marker);
        bounds.extend(position);
    });
    
    // 지도 뷰 조정
    if (routeInfo.bounds) {
        const routeBounds = new google.maps.LatLngBounds(
            new google.maps.LatLng(routeInfo.bounds.southwest.lat, routeInfo.bounds.southwest.lng),
            new google.maps.LatLng(routeInfo.bounds.northeast.lat, routeInfo.bounds.northeast.lng)
        );
        map.fitBounds(routeBounds);
    } else if (locations.length > 0) {
        map.fitBounds(bounds);
    }
    
    // 줌 레벨 조정
    google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
        if (map.getZoom() > 15) {
            map.setZoom(15);
        }
    });
    
    console.log(`Optimized route displayed with ${locations.length} locations`);
}

function displayRoute(places) {
    console.log('displayRoute called with places:', places);
    
    if (!map) {
        console.error('Map not initialized');
        return;
    }
    
    if (places.length === 0) {
        console.log('No places to display');
        return;
    }
    
    // 기존 마커들 제거
    if (window.currentMarkers) {
        window.currentMarkers.forEach(marker => marker.setMap(null));
    }
    window.currentMarkers = [];
    
    // 지도 경계 설정을 위한 bounds 객체
    const bounds = new google.maps.LatLngBounds();
    
    // 각 장소에 마커 추가
    places.forEach((place, index) => {
        const position = new google.maps.LatLng(place.lat, place.lng);
        
        const marker = new google.maps.Marker({
            position: position,
            map: map,
            title: place.name,
            label: (index + 1).toString(),
            icon: {
                url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
                scaledSize: new google.maps.Size(32, 32)
            }
        });
        
        // 정보창 생성
        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div style="max-width: 200px;">
                    <h4 style="margin: 0 0 8px 0; font-weight: bold;">${place.name}</h4>
                    <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">${place.location || ''}</p>
                    <p style="margin: 0; font-size: 11px; color: #888;">클릭하여 상세 정보 보기</p>
                </div>
            `
        });
        
        // 마커 클릭 이벤트
        marker.addListener('click', () => {
            // 다른 정보창들 닫기
            if (window.currentInfoWindow) {
                window.currentInfoWindow.close();
            }
            infoWindow.open(map, marker);
            window.currentInfoWindow = infoWindow;
        });
        
        window.currentMarkers.push(marker);
        bounds.extend(position);
    });
    
    // 지도 뷰를 모든 마커가 보이도록 조정
    if (places.length > 0) {
        map.fitBounds(bounds);
        
        // 줌 레벨이 너무 높으면 조정
        google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
            if (map.getZoom() > 15) {
                map.setZoom(15);
            }
        });
    }
    
    // 경로 표시 (2개 이상의 장소가 있을 때)
    if (places.length >= 2 && directionsService && directionsRenderer) {
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
                // 기존 경로 제거
                directionsRenderer.setDirections({routes: []});
                
                // 새 경로 표시 (마커는 숨기고 경로만 표시)
                const routeRenderer = new google.maps.DirectionsRenderer({
                    directions: result,
                    suppressMarkers: true, // 마커는 이미 표시했으므로 숨김
                    polylineOptions: {
                        strokeColor: '#4285F4',
                        strokeWeight: 4,
                        strokeOpacity: 0.8
                    }
                });
                routeRenderer.setMap(map);
                
                console.log('Route displayed successfully');
            } else {
                console.log('Directions request failed due to ' + status);
            }
        });
    }
    
    console.log(`Displayed ${places.length} places on map`);
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

// 전역 변수 추가
let mapModal, mapSearchInput, autocomplete, selectedPlace;
let currentTravelPlan = null;

// Google Maps API 로드 완료 후 호출되는 콜백 함수
function initializeApp() {
    console.log('Google Maps API loaded, initializing app...');
    initMap();
    initializeDOMEvents();
}

// DOM 이벤트 초기화
function initializeDOMEvents() {
    console.log('Initializing DOM events...');
    
    // 사용자 인증 상태 확인
    checkAuthStatus();
    
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
    
    // 오늘 날짜를 기본값으로 설정
    const today = new Date().toISOString().split('T')[0];
    const startDateEl = document.getElementById('startDate');
    const endDateEl = document.getElementById('endDate');
    
    if (startDateEl) startDateEl.value = today;
    if (endDateEl) endDateEl.value = today;
    
    // 초기 여행 기간 표시
    updateTripDuration();
    
    // 지도 모달 이벤트 등록
    setupMapModalEvents();
    
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
}

// DOM 로드 완료 시 실행 (Google Maps API가 로드되지 않은 경우 대비)
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Google Maps API가 이미 로드된 경우
    if (typeof google !== 'undefined' && google.maps) {
        initializeApp();
    } else {
        // Google Maps API 로드 대기
        console.log('Waiting for Google Maps API to load...');
        let checkCount = 0;
        const checkInterval = setInterval(() => {
            checkCount++;
            if (typeof google !== 'undefined' && google.maps) {
                clearInterval(checkInterval);
                initializeApp();
            } else if (checkCount > 50) { // 5초 후 타임아웃
                clearInterval(checkInterval);
                console.error('Google Maps API failed to load');
                // API 없이도 기본 기능은 동작하도록
                initializeDOMEvents();
            }
        }, 100);
    }
});

function setupOtherEventListeners() {
    // 도시 변경 이벤트 - 도시별 추천 스타일 자동 조정 및 지도 중심점 변경
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
            
            // 지도 중심점 변경
            if (map) {
                const newCenter = getCityCenter();
                map.setCenter(newCenter);
                map.setZoom(DEFAULT_ZOOM);
                console.log(`Map center changed to ${city}:`, newCenter);
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

// 지도 모달 초기화
function initMapModal() {
    // 선택된 도시에 따라 지도 중심점 설정
    const cityCenter = getCityCenter();
    
    mapModal = new google.maps.Map(document.getElementById('mapContainer'), {
        zoom: 13,
        center: cityCenter
    });
    
    // 지도 검색 Autocomplete
    mapSearchInput = document.getElementById('mapSearchInput');
    const mapAutocomplete = new google.maps.places.Autocomplete(mapSearchInput, {
        componentRestrictions: { country: 'kr' },
        fields: ['place_id', 'geometry', 'name', 'formatted_address']
    });
    
    let marker;
    
    mapAutocomplete.addListener('place_changed', () => {
        const place = mapAutocomplete.getPlace();
        if (place.geometry) {
            // 기존 마커 제거
            if (marker) marker.setMap(null);
            
            // 새 마커 추가
            marker = new google.maps.Marker({
                position: place.geometry.location,
                map: mapModal,
                title: place.name
            });
            
            // 지도 중심 이동
            mapModal.setCenter(place.geometry.location);
            mapModal.setZoom(15);
            
            // 선택된 장소 저장
            selectedPlace = {
                name: place.name,
                address: place.formatted_address,
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng()
            };
        }
    });
    
    // 지도 클릭 이벤트
    mapModal.addListener('click', (event) => {
        // 기존 마커 제거
        if (marker) marker.setMap(null);
        
        // 새 마커 추가
        marker = new google.maps.Marker({
            position: event.latLng,
            map: mapModal,
            title: '선택된 위치'
        });
        
        // 선택된 위치 저장
        selectedPlace = {
            name: '선택된 위치',
            address: `위도: ${event.latLng.lat().toFixed(6)}, 경도: ${event.latLng.lng().toFixed(6)}`,
            lat: event.latLng.lat(),
            lng: event.latLng.lng()
        };
    });
}

// 지도 모달 이벤트 설정
function setupMapModalEvents() {
    // 지도 검색 버튼 클릭
    document.getElementById('mapSearchBtn').addEventListener('click', () => {
        document.getElementById('mapModal').classList.remove('hidden');
        // 지도 모달 초기화
        setTimeout(() => {
            if (!mapModal) {
                initMapModal();
            }
        }, 100);
    });
    
    // 모달 닫기
    document.getElementById('closeMapModal').addEventListener('click', () => {
        document.getElementById('mapModal').classList.add('hidden');
    });
    
    // 취소 버튼
    document.getElementById('cancelMapSelection').addEventListener('click', () => {
        document.getElementById('mapModal').classList.add('hidden');
    });
    
    // 선택 완료 버튼
    document.getElementById('confirmMapSelection').addEventListener('click', () => {
        if (selectedPlace) {
            document.getElementById('startLocation').value = selectedPlace.address;
            document.getElementById('mapModal').classList.add('hidden');
            console.log('출발지 선택 완료:', selectedPlace);
        } else {
            alert('위치를 선택해주세요.');
        }
    });
}

// 도시별 지도 중심점 가져오기
function getCityCenter() {
    const cityEl = document.getElementById('city');
    const selectedCity = cityEl ? cityEl.value : 'Seoul';
    
    const cityCenters = {
        'Seoul': { lat: 37.5665, lng: 126.9780 },
        'Busan': { lat: 35.1796, lng: 129.0756 },
        'Daegu': { lat: 35.8714, lng: 128.6014 },
        'Incheon': { lat: 37.4563, lng: 126.7052 },
        'Gwangju': { lat: 35.1595, lng: 126.8526 },
        'Daejeon': { lat: 36.3504, lng: 127.3845 },
        'Ulsan': { lat: 35.5384, lng: 129.3114 },
        'Jeju': { lat: 33.4996, lng: 126.5312 },
        'Suwon': { lat: 37.2636, lng: 127.0286 },
        'Chuncheon': { lat: 37.8813, lng: 127.7298 },
        'Gangneung': { lat: 37.7519, lng: 128.8761 },
        'Jeonju': { lat: 35.8242, lng: 127.1480 },
        'Yeosu': { lat: 34.7604, lng: 127.6622 },
        'Gyeongju': { lat: 35.8562, lng: 129.2247 },
        'Andong': { lat: 36.5684, lng: 128.7294 }
    };
    
    return cityCenters[selectedCity] || SEOUL_CENTER;
}

// 사용자 인증 상태 확인
function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    if (token) {
        // 로그인 상태
        document.getElementById('authButtons').classList.add('hidden');
        document.getElementById('userInfo').classList.remove('hidden');
        document.getElementById('userName').textContent = '사용자';
        
        // 로그아웃 이벤트
        document.getElementById('logoutBtn').onclick = function() {
            localStorage.removeItem('access_token');
            location.reload();
        };
    }
}

// 날씨 정보 표시
function displayWeatherInfo(weatherInfo) {
    const weatherDiv = document.getElementById('weatherInfo');
    const weatherContent = document.getElementById('weatherContent');
    
    const weatherIcon = getWeatherIcon(weatherInfo.condition);
    const tempColor = weatherInfo.temperature > 25 ? 'text-red-500' : 
                     weatherInfo.temperature < 10 ? 'text-blue-500' : 'text-green-500';
    
    weatherContent.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-2">
                <span class="text-2xl">${weatherIcon}</span>
                <span class="text-lg font-medium">${weatherInfo.condition}</span>
            </div>
            <span class="text-2xl font-bold ${tempColor}">${weatherInfo.temperature}°C</span>
        </div>
        <div class="grid grid-cols-2 gap-2 text-sm text-gray-600">
            <div><i class="fas fa-thermometer-half"></i> 체감: ${weatherInfo.feels_like}°C</div>
            <div><i class="fas fa-tint"></i> 습도: ${weatherInfo.humidity}%</div>
            <div><i class="fas fa-wind"></i> 바람: ${weatherInfo.wind_speed}m/s</div>
            <div><i class="fas fa-eye"></i> 가시거리: ${weatherInfo.visibility}km</div>
        </div>
        ${weatherInfo.rain_probability > 0 ? `
            <div class="mt-3 p-2 bg-blue-50 rounded">
                <span class="text-sm text-blue-700">
                    <i class="fas fa-umbrella"></i> 강수확률: ${weatherInfo.rain_probability}%
                </span>
            </div>
        ` : ''}
        <div class="mt-3 p-2 bg-green-50 rounded">
            <span class="text-sm text-green-700">
                <i class="fas fa-lightbulb"></i> ${weatherInfo.recommendation}
            </span>
        </div>
    `;
    
    weatherDiv.classList.remove('hidden');
}

function getWeatherIcon(condition) {
    const icons = {
        '맑음': '☀️',
        '구름조금': '🌤️', 
        '구름많음': '☁️',
        '흐림': '☁️',
        '비': '🌧️',
        '소나기': '🌦️',
        '눈': '❄️',
        '안개': '🌫️'
    };
    
    for (const [key, icon] of Object.entries(icons)) {
        if (condition.includes(key)) {
            return icon;
        }
    }
    return '🌤️';
}

// 경로 표시 함수들
function displayRouteWithTransportation(itinerary) {
    const startLocation = selectedPlace ? selectedPlace.address : document.getElementById('startLocation').value;
    if (!startLocation.trim()) {
        // 출발지가 없으면 일반 마커만 표시
        displayMarkersOnly(itinerary);
        return;
    }
    
    // 출발지에서 첫 번째 장소로의 경로 표시
    if (itinerary.length > 0) {
        const destination = itinerary[0];
        displayMultipleRoutes(startLocation, destination);
    }
    
    // 모든 장소에 마커 표시
    displayMarkersOnly(itinerary);
}

function displayMultipleRoutes(start, destination) {
    const modes = [
        { mode: google.maps.TravelMode.TRANSIT, color: '#4285F4', name: '대중교통' },
        { mode: google.maps.TravelMode.DRIVING, color: '#EA4335', name: '자동차' },
        { mode: google.maps.TravelMode.WALKING, color: '#34A853', name: '도보' }
    ];
    
    modes.forEach((transport, index) => {
        const request = {
            origin: start,
            destination: `${destination.address || destination.location}`,
            travelMode: transport.mode
        };
        
        directionsService.route(request, (result, status) => {
            if (status === 'OK') {
                const renderer = new google.maps.DirectionsRenderer({
                    directions: result,
                    routeIndex: 0,
                    polylineOptions: {
                        strokeColor: transport.color,
                        strokeWeight: 4,
                        strokeOpacity: 0.7
                    },
                    suppressMarkers: index > 0 // 첫 번째만 마커 표시
                });
                renderer.setMap(map);
                
                // 경로 정보 표시
                const route = result.routes[0];
                const leg = route.legs[0];
                console.log(`${transport.name}: ${leg.distance.text}, ${leg.duration.text}`);
            }
        });
    });
}

function displayMarkersOnly(itinerary) {
    console.log('displayMarkersOnly called with itinerary:', itinerary);
    
    if (!map) {
        console.error('Map not initialized');
        return;
    }
    
    if (!itinerary || itinerary.length === 0) {
        console.log('No itinerary to display');
        return;
    }
    
    // 기존 마커들 제거
    if (window.currentMarkers) {
        window.currentMarkers.forEach(marker => marker.setMap(null));
    }
    window.currentMarkers = [];
    
    const bounds = new google.maps.LatLngBounds();
    
    itinerary.forEach((item, index) => {
        const lat = item.lat || 37.5665;
        const lng = item.lng || 126.9780;
        const position = new google.maps.LatLng(lat, lng);
        
        const marker = new google.maps.Marker({
            position: position,
            map: map,
            title: item.place_name || item.name || item.activity,
            label: (index + 1).toString(),
            icon: {
                url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                scaledSize: new google.maps.Size(32, 32)
            }
        });
        
        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div style="max-width: 250px;">
                    <h4 style="margin: 0 0 8px 0; font-weight: bold; color: #1a73e8;">${item.place_name || item.name || item.activity}</h4>
                    <p style="margin: 0 0 4px 0; font-size: 13px; color: #333;">${item.description || ''}</p>
                    <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">
                        <i class="fas fa-map-marker-alt" style="color: #ea4335;"></i> ${item.address || item.location || ''}
                    </p>
                    ${item.rating ? `<p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">
                        <i class="fas fa-star" style="color: #fbbc04;"></i> ${item.rating}/5
                    </p>` : ''}
                    ${item.time ? `<p style="margin: 0; font-size: 11px; color: #888;">
                        <i class="fas fa-clock"></i> ${item.time} (${item.duration || '30분'})
                    </p>` : ''}
                </div>
            `
        });
        
        marker.addListener('click', () => {
            // 다른 정보창들 닫기
            if (window.currentInfoWindow) {
                window.currentInfoWindow.close();
            }
            infoWindow.open(map, marker);
            window.currentInfoWindow = infoWindow;
        });
        
        window.currentMarkers.push(marker);
        bounds.extend(position);
    });
    
    // 지도 뷰 조정
    if (itinerary.length > 0) {
        map.fitBounds(bounds);
        
        // 줌 레벨 조정
        google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
            if (map.getZoom() > 15) {
                map.setZoom(15);
            }
        });
    }
    
    console.log(`Displayed ${itinerary.length} markers on map`);
}

// 여행 계획 저장 기능
function setupSaveFeatures() {
    // 내 여행 계획에 저장
    document.getElementById('savePlanBtn').onclick = async function() {
        if (!currentTravelPlan) {
            alert('저장할 여행 계획이 없습니다.');
            return;
        }
        
        const token = localStorage.getItem('access_token');
        if (!token) {
            alert('로그인이 필요합니다.');
            window.location.href = 'login.html';
            return;
        }
        
        try {
            const response = await fetch('/api/users/travel-plans', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    title: currentTravelPlan.title,
                    city: currentTravelPlan.preferences?.city || 'Seoul',
                    itinerary_json: JSON.stringify(currentTravelPlan.itinerary),
                    total_cost: currentTravelPlan.total_cost?.amount || 0
                })
            });
            
            if (response.ok) {
                showSaveResult('내 여행 계획에 저장되었습니다!', 'success');
            } else {
                showSaveResult('저장에 실패했습니다.', 'error');
            }
        } catch (error) {
            showSaveResult('오류: ' + error.message, 'error');
        }
    };
    
    // Notion에 저장
    document.getElementById('saveNotionBtn').onclick = async function() {
        if (!currentTravelPlan) {
            alert('저장할 여행 계획이 없습니다.');
            return;
        }
        
        try {
            const response = await fetch('/api/travel/save-notion', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(currentTravelPlan)
            });
            
            const result = await response.json();
            if (result.success) {
                showSaveResult(`Notion에 저장되었습니다! <a href="${result.url}" target="_blank" class="text-blue-500 hover:underline">보기</a>`, 'success');
            } else {
                showSaveResult('Notion 저장에 실패했습니다.', 'error');
            }
        } catch (error) {
            showSaveResult('오류: ' + error.message, 'error');
        }
    };
    
    // 예산 계산
    document.getElementById('calculateBudgetBtn').onclick = async function() {
        if (!currentTravelPlan || !currentTravelPlan.itinerary) {
            alert('계산할 여행 계획이 없습니다.');
            return;
        }
        
        const budgetStyle = document.getElementById('budgetStyle').value;
        
        try {
            const response = await fetch('/api/users/calculate-budget', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    itinerary: currentTravelPlan.itinerary,
                    travel_style: budgetStyle
                })
            });
            
            const budget = await response.json();
            showBudgetResult(budget);
        } catch (error) {
            alert('예산 계산 오류: ' + error.message);
        }
    };
}

function showSaveResult(message, type) {
    const saveResult = document.getElementById('saveResult');
    saveResult.className = `mt-3 p-2 rounded ${type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`;
    saveResult.innerHTML = message;
    saveResult.classList.remove('hidden');
}

function showBudgetResult(budget) {
    const budgetResult = document.getElementById('budgetResult');
    budgetResult.innerHTML = `
        <div class="p-3 bg-orange-50 rounded">
            <h4 class="font-semibold text-orange-800 mb-2">예상 비용: ${budget.total_cost.toLocaleString()}원</h4>
            <div class="text-sm text-orange-700 space-y-1">
                <div>교통비: ${budget.breakdown.transportation.toLocaleString()}원</div>
                <div>음식비: ${budget.breakdown.food.toLocaleString()}원</div>
                <div>관광비: ${budget.breakdown.attractions.toLocaleString()}원</div>
                <div>숙박비: ${budget.breakdown.accommodation.toLocaleString()}원</div>
                <div>기타: ${budget.breakdown.miscellaneous.toLocaleString()}원</div>
            </div>
            ${budget.recommendations ? `
                <div class="mt-2 text-xs text-orange-600">
                    ${budget.recommendations.slice(0, 3).map(rec => `<div>• ${rec}</div>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
    budgetResult.classList.remove('hidden');
}

// displayResults 함수 오버라이드
async function displayResults(data) {
    currentTravelPlan = data;
    setupSaveFeatures();
    
    hideLoading();
    
    document.getElementById('results').classList.remove('hidden');
    
    // Initialize map if not already done
    if (!map) {
        initMap();
    }
    
    // 일자별 탭 초기화
    currentDay = 1;
    
    // Display timeline with day tabs
    displayTimeline(data.itinerary || []);
    
    // Verify places and get details for current day
    await verifyAndDisplayPlaces(dayGroups[currentDay] || []);
    
    // Show optimized route on map - 8단계 아키텍처 지원
    console.log('Displaying route with places:', places);
    console.log('API response data structure:', data);
    
    // 8단계 처리된 경로 정보 확인
    const routeInfo = data.total_cost?.route_info || data.route_info || data.processing_metadata?.optimized_route;
    
    if (routeInfo && routeInfo.polyline) {
        console.log('Using optimized route from 8-step architecture');
        displayOptimizedRoute(routeInfo);
    } else if (places && places.length > 0) {
        console.log('Using places array for route display');
        displayRoute(places);
    } else {
        console.log('Displaying markers only from itinerary');
        // 8단계 처리된 일정으로 마커 표시
        displayMarkersOnly(data.itinerary || []);
    }
    
    // 8단계 처리 결과 로그
    if (data.processing_metadata) {
        console.log('8-step processing metadata:', data.processing_metadata);
    }
    
    // 날씨 정보 표시
    if (data.weather_info) {
        displayWeatherInfo(data.weather_info);
    }
    
    // Show Notion saving status
    updateNotionStatus('saving');
    
    // Notion 저장 상태 업데이트
    setTimeout(() => {
        const url = data.notion_url || 'https://notion.so/sample-page';
        updateNotionStatus('success', url);
    }, NOTION_SAVE_DELAY);
}