import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { API_URL } from "./config.js";
import "./style.css";

// Bilingual Dictionary (Simple everyday English & Tamil)
const I18N = {
  en: {
    appTitle: "VayuNet",
    tagline: "Clean Air Intelligence",
    checking: "Checking…",
    analyzing: "Analyzing hyper-local conditions…",
    locating: "Getting your location…",
    gettingLoc: "Getting your location…",
    loadingTitle: "Checking your area…",
    loadingSub: "Getting satellite and weather data…",
    retryBtn: "Check Again",
    yourLocation: "YOUR LOCATION",
    updateLocBtn: "Update my location",
    gpsDeviceLoc: "GPS: Device Location",
    latitudeLabel: "Latitude",
    longitudeLabel: "Longitude",
    airGood: "AIR IS GOOD",
    airGoodSub: "No significant nearby pollution hotspot detected.",
    airGoodAction: "Air is safe for normal outdoor activities.",
    pollutionNearby: "POLLUTION NEARBY",
    pollutionNearbySub: "A pollution hotspot was detected nearby. Current wind does not indicate movement toward your area.",
    pollutionNearbyAction: "Air in your immediate area is safe. Monitor for wind direction changes.",
    attention: "ATTENTION",
    attentionSub: "A nearby pollution hotspot is currently aligned with the prevailing wind toward your area. Consider checking the affected-area map.",
    attentionAction: "Stay indoors if possible and follow local official advisories.",
    whyAlertTitle: "WHY THIS ALERT?",
    whyAlertDefault: "Atmospheric data and wind vectors are being analyzed for your area.",
    mapTitle: "LIVE POLLUTION MAP",
    legendUser: "🔵 Blue = You / Current Location",
    legendHotspot: "🔴 Red = Pollution Hotspot",
    legendMove: "🟠 Orange = Possible Pollution Movement",
    legendAffected: "🟡 Yellow = Potentially Affected Area",
    legendArrow: "🌬️ Arrow = Wind / Movement Direction",
    movementTitle: "Possible pollution movement",
    movementDefault: "Calculating possible movement from wind…",
    movementFromHotspot: "Pollution moving from hotspot toward",
    windToward: "Wind blowing toward",
    affectedTitle: "Potentially affected area",
    userMayBeAffected: "Pollution may affect your area.",
    userNotAffected: "Your area is not currently in the direct downwind path.",
    downwindUnavailable: "Downwind analysis unavailable",
    downwindUnavailableSub: "Wind data is currently unavailable, so pollution movement and affected-area estimation cannot be determined.",
    whatToDoTitle: "What you should do",
    prioritySitesTitle: "Places to verify (Downwind)",
    lastUpdated: "Last updated",
    checkAgainBtn: "Check again",
    techDetailsTitle: "Technical details (Scientific)",
    no2Column: "NO₂ Column",
    so2Column: "SO₂ Column",
    windSpeedDir: "Wind (Speed & Direction)",
    tempHumidity: "Temperature & Humidity",
    obsTime: "Observation Time",
    anomalyScore: "Anomaly Score",
    dataSource: "Data Source",
    geeStatus: "Satellite Status",
    userCoords: "Coordinates",
    satelliteData: "Satellite data",
    satelliteUnavailable: "Satellite pollution data unavailable",
    weatherUnavailable: "Wind data unavailable",
    noHotspot: "No nearby pollution hotspot detected.",
    realSatelliteBadge: "REAL SATELLITE",
    demoBadge: "DEMO MODE",
    widgetTitle: "Android Home-Screen Widget Preview",
    alertBtnLabel: "Enable Alert Sound & Notifications",
    alertBtnActive: "Alerts & Notifications Active ✓",
    disclaimer: "Scientific Notice: VayuNet provides decision-support and awareness using satellite atmospheric columns and weather models. It does not replace official government pollution advisories.",
    reportBtn: "📸 Report Visible Pollution",
    reportTitle: "Citizen Pollution Observation",
    reportSub: "Take or upload a photo of visible smoke, haze, or emissions. Your current GPS coordinates will be attached automatically.",
    photoLabel: "Photo (Citizen Evidence)",
    takePhotoBtn: "Take / Choose Photo",
    photoSelected: "Photo ready for assessment",
    coordsAttached: "📍 GPS Coordinates Attached",
    categoryLabel: "Pollution Category",
    catSmoke: "Smoke / Heavy Haze",
    catFire: "Agricultural / Waste Fire",
    catIndustrial: "Industrial / Factory Plume",
    catDust: "Dust / Construction Plume",
    catOther: "Other Visible Pollution",
    descLabel: "Short Description (Optional)",
    descPlaceholder: "e.g. Heavy black smoke from open burning near highway...",
    submitObservation: "Submit Citizen Evidence",
    submitting: "Analyzing & Submitting…",
    observationNotice: "Notice: Citizen photos serve as qualitative ground evidence. They do not measure chemical gas concentrations (NO₂/SO₂).",
    legendCitizen: "🟣 Purple = Citizen Observation",
    citizenObsTitle: "CITIZEN POLLUTION OBSERVATIONS",
    noCitizenObs: "No citizen observations recorded within 15 km yet.",
    recentObsSubtitle: "Recent community visual reports within 15 km",
    viewPhoto: "View Photo Evidence",
    aiAssessmentLabel: "AI Visual Assessment",
    groundVerificationReq: "Requires Ground Verification"
  },
  ta: {
    appTitle: "வாயுநெட்",
    tagline: "சுத்தமான காற்று வழிகாட்டி",
    checking: "ஆய்வு செய்கிறது…",
    analyzing: "உங்கள் பகுதியை ஆய்வு செய்கிறது…",
    locating: "உங்கள் இருப்பிடம் பெறப்படுகிறது…",
    gettingLoc: "உங்கள் இருப்பிடம் பெறப்படுகிறது…",
    loadingTitle: "உங்கள் பகுதியை ஆய்வு செய்கிறது…",
    loadingSub: "செயற்கைக்கோள் மற்றும் வானிலை தகவல்கள் பெறப்படுகின்றன…",
    retryBtn: "மீண்டும் முயற்சிக்கவும்",
    yourLocation: "உங்கள் இடம்",
    updateLocBtn: "என் இடத்தை புதுப்பி",
    gpsDeviceLoc: "ஜிபிஎஸ்: சாதன அமைவிடம்",
    latitudeLabel: "அட்சரேகை",
    longitudeLabel: "தீர்க்கரேகை",
    airGood: "காற்று சுத்தமாக உள்ளது",
    airGoodSub: "அருகில் குறிப்பிடத்தக்க காற்று மாசு மையம் எதுவும் இல்லை.",
    airGoodAction: "வெளிப்புற நடவடிக்கைகளுக்கு காற்று பாதுகாப்பாக உள்ளது.",
    pollutionNearby: "அருகில் காற்று மாசு உள்ளது",
    pollutionNearbySub: "அருகில் காற்று மாசு கண்டறியப்பட்டுள்ளது. தற்போதைய காற்று உங்கள் பகுதியை நோக்கி வீசவில்லை.",
    pollutionNearbyAction: "உங்கள் பகுதியில் காற்று தற்போது பாதுகாப்பாக உள்ளது. நிலவரத்தை கவனிக்கவும்.",
    attention: "கவனமாக இருக்கவும்",
    attentionSub: "அருகில் உள்ள காற்று மாசு மையம், தற்போதைய காற்று வீசும் திசையால் உங்கள் பகுதியை நோக்கி நகர வாய்ப்புள்ளது. வரைபடத்தை பார்க்கவும்.",
    attentionAction: "முடிந்தவரை வீட்டிற்குள் இருக்கவும், அரசு வழிகாட்டுதல்களைப் பின்பற்றவும்.",
    whyAlertTitle: "இந்த எச்சரிக்கை ஏன்?",
    whyAlertDefault: "உங்கள் பகுதிக்கான செயற்கைக்கோள் மற்றும் காற்றின் திசை ஆய்வு செய்யப்படுகிறது.",
    mapTitle: "நேரடி காற்று மாசு வரைபடம்",
    legendUser: "🔵 நீலம் = நீங்கள் / உங்கள் இடம்",
    legendHotspot: "🔴 சிவப்பு = மாசு மையம்",
    legendMove: "🟠 ஆரஞ்சு = மாசு செல்லும் பாதை",
    legendAffected: "🟡 மஞ்சள் = பாதிக்கப்படக்கூடிய பகுதி",
    legendArrow: "🌬️ அம்பு = காற்றின் திசை / நகரும் திசை",
    movementTitle: "மாசு செல்லக்கூடிய திசை",
    movementDefault: "காற்றின் அடிப்படையில் திசை கணிக்கப்படுகிறது…",
    movementFromHotspot: "மாசு மையத்திலிருந்து நகரும் திசை",
    windToward: "காற்று வீசும் திசை",
    affectedTitle: "பாதிக்கப்படக்கூடிய பகுதி",
    userMayBeAffected: "காற்று செல்லும் பாதையில் உங்கள் பகுதி அமைய வாய்ப்புள்ளது.",
    userNotAffected: "உங்கள் பகுதி காற்று செல்லும் நேரடிப் பாதையில் இல்லை.",
    downwindUnavailable: "காற்றுப் பாதை பகுப்பாய்வு கிடைக்கவில்லை",
    downwindUnavailableSub: "காற்றின் தகவல் தற்போது கிடைக்காததால், மாசு நகர்வு மற்றும் பாதிக்கப்படக்கூடிய பகுதியை கணிக்க இயலவில்லை.",
    whatToDoTitle: "நீங்கள் என்ன செய்ய வேண்டும்?",
    prioritySitesTitle: "சரிபார்க்க வேண்டிய இடங்கள்",
    lastUpdated: "கடைசியாக புதுப்பிக்கப்பட்டது",
    checkAgainBtn: "மீண்டும் பார்க்கவும்",
    techDetailsTitle: "தொழில்நுட்ப விவரங்கள்",
    no2Column: "NO₂ அளவு",
    so2Column: "SO₂ அளவு",
    windSpeedDir: "காற்று (வேகம் & திசை)",
    tempHumidity: "வெப்பநிலை & ஈரப்பதம்",
    obsTime: "கண்காணிப்பு நேரம்",
    anomalyScore: "மாசு குறியீடு",
    dataSource: "தரவு மூலம்",
    geeStatus: "செயற்கைக்கோள் நிலை",
    userCoords: "அமைவிடம்",
    satelliteData: "செயற்கைக்கோள் தரவு",
    satelliteUnavailable: "செயற்கைக்கோள் மாசு தரவு தற்காலிகமாக கிடைக்கவில்லை",
    weatherUnavailable: "காற்றின் திசை மற்றும் வானிலை தகவல் கிடைக்கவில்லை",
    noHotspot: "அருகில் குறிப்பிடத்தக்க காற்று மாசு மையம் இல்லை.",
    realSatelliteBadge: "நேரடி செயற்கைக்கோள்",
    demoBadge: "மாதிரி முறை (DEMO)",
    widgetTitle: "ஆண்ட்ராய்டு விட்ஜெட் முன்னோட்டம்",
    alertBtnLabel: "ஒலி மற்றும் அறிவிப்புகளை இயக்கவும்",
    alertBtnActive: "அறிவிப்புகள் இயக்கப்பட்டுள்ளன ✓",
    disclaimer: "அறிவிப்பு: வாயுநெட் பொது விழிப்புணர்வு மற்றும் வழிகாட்டுதலுக்காக மட்டுமே. இது அரசு அதிகாரப்பூர்வ எச்சரிக்கைகளுக்கு மாற்றாகாது.",
    reportBtn: "📸 காற்று மாசை பதிவு செய்",
    reportTitle: "பொதுமக்கள் காற்று மாசு பதிவு",
    reportSub: "புகை, புழுதி அல்லது மாசின் புகைப்படத்தை பதிவேற்றவும். உங்கள் ஜிபிஎஸ் தானாக இணைக்கப்படும்.",
    photoLabel: "புகைப்படம் (ஆதாரம்)",
    takePhotoBtn: "புகைப்படம் எடு / தேர்வு செய்",
    photoSelected: "புகைப்படம் தயாராக உள்ளது",
    coordsAttached: "📍 ஜிபிஎஸ் இணைக்கப்பட்டது",
    categoryLabel: "மாசு வகை",
    catSmoke: "புகை / அடர் மூடுபனி",
    catFire: "விவசாய / குப்பை எரிப்பு",
    catIndustrial: "தொழிற்சாலை புகை",
    catDust: "புழுதி / கட்டுமான தூசு",
    catOther: "மற்றவை",
    descLabel: "விவரம் (விருப்பத்தேர்வு)",
    descPlaceholder: "எ.கா. சாலையோரத்தில் எரிக்கப்படும் கழிவுகளிலிருந்து வரும் புகை...",
    submitObservation: "பதிவை சமர்ப்பிக்கவும்",
    submitting: "ஆய்வு செய்து சமர்ப்பிக்கிறது…",
    observationNotice: "அறிவிப்பு: பொதுமக்கள் புகைப்படங்கள் நேரடி பார்வைக் கள ஆதாரமாக மட்டுமே பயன்படும்; வாயு அளவீடுகள் அல்ல.",
    legendCitizen: "🟣 ஊதா = பொதுமக்கள் நேரடி பதிவு",
    citizenObsTitle: "பொதுமக்கள் நேரடி பதிவுகள்",
    noCitizenObs: "15 கி.மீ சுற்றளவில் பொதுமக்கள் பதிவுகள் எதுவும் இல்லை.",
    recentObsSubtitle: "அருகிலுள்ள பொதுமக்கள் பார்வை ஆதாரங்கள் (15 கி.மீ)",
    viewPhoto: "புகைப்பட ஆதாரத்தைப் பார்க்கவும்",
    aiAssessmentLabel: "AI காட்சி மதிப்பீடு",
    groundVerificationReq: "கள ஆய்வு தேவை"
  }
};

let currentLang = localStorage.getItem("vayunet_lang") || "en";
function t(key) {
  return I18N[currentLang]?.[key] || I18N["en"]?.[key] || key;
}

// State
let map = null;
let userMarker = null;
let hotspotMarker = null;
let movementArrowMarker = null;
let corridorLayer = null;
let affectedLayer = null;
let movementPathLayer = null;
let sensitiveMarkers = [];
let citizenMarkers = [];
let selectedCitizenCategory = "smoke_haze";
let currentPhotoBase64 = null;
let currentLat = null;
let currentLon = null;
let lastAnalysisData = null;
let audioContext = null;

// Build DOM Structure ONCE (Preserves #map container so Leaflet NEVER breaks)
function createDOMShellOnce() {
  const app = document.querySelector("#app");
  if (!app) return;

  app.innerHTML = `
  <div class="shell">
    <!-- 1. Header -->
    <header>
      <div class="brand-wrap">
        <div class="brand-icon">
          <img src="/vayunet-logo.png" alt="VayuNet" class="brand-logo-img">
        </div>
        <div class="brand-text">
          <h1 id="txtAppTitle">VayuNet</h1>
          <p id="txtTagline">Clean Air Intelligence</p>
        </div>
      </div>
      <div class="header-controls">
        <div class="lang-toggle">
          <button id="langEnBtn" class="lang-btn ${currentLang === 'en' ? 'active' : ''}">EN</button>
          <button id="langTaBtn" class="lang-btn ${currentLang === 'ta' ? 'active' : ''}">தமிழ்</button>
        </div>
        <span id="modeBadge" class="badge-mode loading">CHECKING…</span>
        <button id="refreshBtn" class="btn-icon" title="Refresh">↻</button>
      </div>
    </header>

    <!-- 2. Your Location Section (Fresh Device GPS - No hardcoded city) -->
    <section class="location-section">
      <div class="loc-top-row">
        <div class="loc-title">
          <span>📍</span>
          <span id="txtYourLocation">YOUR LOCATION</span>
        </div>
        <button id="locateMeBtn" class="loc-update-btn">
          <span>📍</span>
          <span id="txtUpdateLocBtn">Update my location</span>
        </button>
      </div>
      <div id="locPlaceName" class="loc-place-name">📍 Getting your location...</div>
      <div class="loc-gps-box">
        <div id="txtGpsTag" class="loc-gps-tag">GPS: Device Location</div>
        <div class="loc-coords-row">
          <span id="locLatDisplay">Latitude: —</span>
          <span id="locLonDisplay">Longitude: —</span>
        </div>
      </div>
    </section>

    <!-- 2b. Report Visible Pollution (Citizen Observation) Quick Action -->
    <div class="citizen-action-wrap">
      <button id="btnOpenCitizenReport" class="btn-report-action" type="button">
        <span>📸</span>
        <span id="txtReportBtn">Report Visible Pollution</span>
      </button>
    </div>

    <!-- Citizen Observation Submission Form (Collapsible) -->
    <section id="citizenReportSection" class="citizen-report-section hidden">
      <div class="citizen-report-header">
        <div class="citizen-report-title">
          <span>📸</span>
          <span id="txtReportTitle">Citizen Pollution Observation</span>
        </div>
        <button id="btnCloseCitizenReport" class="btn-close-form" type="button" title="Close">✕</button>
      </div>
      <p id="txtReportSub" class="citizen-report-sub">
        Take or upload a photo of visible smoke, haze, or emissions. Your current GPS coordinates will be attached automatically.
      </p>

      <!-- Photo Picker Box -->
      <div id="photoDropArea" class="photo-upload-box">
        <input type="file" id="citizenPhotoInput" accept="image/*" capture="environment" style="display: none;" />
        <div class="upload-icon">📷</div>
        <div id="txtUploadPrompt" class="upload-prompt">Tap to Take or Upload Photo</div>
        <div class="upload-hint">Smoke plume, crop burning, factory emission, or dust</div>
      </div>

      <div id="photoPreviewWrap" class="photo-preview-container hidden">
        <img id="citizenPhotoPreview" class="photo-preview-img" alt="Preview" />
        <button id="btnRemovePhoto" class="btn-remove-photo" type="button" title="Remove photo">✕</button>
      </div>

      <!-- Attached GPS Badge -->
      <div class="attached-gps-badge">
        <span>📍</span>
        <span id="txtAttachedGps">GPS: Awaiting device location fix...</span>
      </div>

      <!-- Category Picker -->
      <div class="category-picker-label" id="txtCategoryLabel">Pollution Category</div>
      <div class="category-grid" id="categoryGrid">
        <button type="button" class="category-chip active" data-cat="smoke_haze">🌫️ <span id="txtCatSmoke">Smoke / Heavy Haze</span></button>
        <button type="button" class="category-chip" data-cat="agricultural_fire">🔥 <span id="txtCatFire">Agricultural / Waste Fire</span></button>
        <button type="button" class="category-chip" data-cat="industrial_emission">🏭 <span id="txtCatIndustrial">Industrial / Factory Plume</span></button>
        <button type="button" class="category-chip" data-cat="dust">💨 <span id="txtCatDust">Dust / Construction Plume</span></button>
      </div>

      <!-- Optional Short Description -->
      <textarea id="citizenDescription" class="desc-textarea" placeholder="Short description (e.g. dense black smoke rising from factory chimney)..." maxlength="300"></textarea>

      <!-- Submit Button & Assessment Notice -->
      <button id="btnSubmitCitizenReport" class="btn-submit-report" type="button" disabled>
        <span id="txtSubmitBtn">Submit Citizen Evidence</span>
      </button>

      <p class="scientific-disclaimer-small" id="txtObsNotice">
        Notice: Citizen photos serve as qualitative ground evidence. They do not measure chemical gas concentrations (NO₂/SO₂).
      </p>

      <!-- Immediate Assessment Result Box -->
      <div id="assessmentResultCard" class="assessment-result-card hidden">
        <div class="assessment-result-head">
          <span>🔍</span>
          <span id="assessmentResultHeadline">AI Visual Assessment</span>
        </div>
        <p id="assessmentResultBody" class="assessment-result-text"></p>
      </div>
    </section>

    <!-- 3. Alert Status Card -->
    <section id="heroCard" class="hero-status-card GOOD">
      <div class="hero-header-row">
        <span id="heroIcon" class="hero-status-icon">🟢</span>
        <h2 id="heroTitle" class="hero-status-title">AIR IS GOOD</h2>
      </div>
      <div id="heroSub" class="hero-status-sub">No significant nearby pollution hotspot detected.</div>
    </section>

    <!-- 4. WHY THIS ALERT? -->
    <section class="why-alert-card">
      <div class="section-label">
        <span>💡</span>
        <span id="txtWhyAlertTitle">WHY THIS ALERT?</span>
      </div>
      <p id="whyAlertText" class="why-alert-text">Atmospheric data and wind vectors are being analyzed for your area.</p>
    </section>

    <!-- 5. LIVE POLLUTION MAP -->
    <section class="map-card">
      <div class="map-header">
        <div class="section-label">
          <span>🗺️</span>
          <span id="txtMapTitle">LIVE POLLUTION MAP</span>
        </div>
      </div>
      <div id="map"></div>
      <div class="map-legend">
        <div class="legend-row">
          <div class="legend-item"><span class="legend-dot user"></span><span id="txtLegUser">🔵 Blue = You / Current Location</span></div>
          <div class="legend-item"><span class="legend-dot hotspot"></span><span id="txtLegHotspot">🔴 Red = Pollution Hotspot</span></div>
        </div>
        <div class="legend-row">
          <div class="legend-item"><span class="legend-dot movement"></span><span id="txtLegMove">🟠 Orange = Possible Pollution Movement</span></div>
          <div class="legend-item"><span class="legend-dot affected"></span><span id="txtLegAffected">🟡 Yellow = Potentially Affected Area</span></div>
        </div>
        <div class="legend-row">
          <div class="legend-item"><span class="legend-dot arrow">➤</span><span id="txtLegArrow">🌬️ Arrow = Wind / Movement Direction</span></div>
        </div>
        <div class="legend-row">
          <div class="legend-item"><span class="legend-dot citizen">📷</span><span id="txtLegCitizen">🟣 Purple = Citizen Observation</span></div>
        </div>
      </div>
    </section>

    <!-- 6. Pollution Movement Card -->
    <section class="movement-card">
      <div id="movementCompass" class="movement-compass-wrap">⬆️</div>
      <div class="movement-info">
        <div id="txtMoveTitle" class="movement-title">Possible pollution movement</div>
        <div id="movementHeading" class="movement-heading">Calculating possible movement from wind…</div>
        <div id="movementSub" class="movement-sub">Surface wind speed and direction</div>
      </div>
    </section>

    <!-- 7. Potentially Affected Area Card -->
    <section class="affected-card">
      <div id="affectedIcon" class="affected-icon">ℹ️</div>
      <div class="affected-info">
        <div id="txtAffTitle" class="affected-title">Potentially affected area</div>
        <div id="affectedStatus" class="affected-status">Downwind analysis unavailable</div>
        <div id="affectedSub" class="affected-sub">Wind data is currently unavailable, so pollution movement and affected-area estimation cannot be determined.</div>
      </div>
    </section>

    <!-- 8. What You Should Do Card -->
    <section id="actionCard" class="action-card">
      <div class="action-header">
        <span id="actionAlertIcon">🛡️</span>
        <span id="actionAlertLabel">What you should do</span>
      </div>
      <div id="actionText" class="action-text">Air is safe for normal outdoor activities.</div>
    </section>

    <!-- Priority Sites (if detected) -->
    <section id="sitesSection" class="sites-card hidden">
      <div class="section-label">
        <span>🏥</span>
        <span id="txtSitesTitle">Places to verify (Downwind)</span>
      </div>
      <div id="sitesList" class="sites-list"></div>
    </section>

    <!-- 9. Last Updated Bar -->
    <section class="update-bar">
      <div class="update-time-wrap">
        <span id="txtLastUpdated">Last updated</span>:
        <strong id="updateTimeDisplay">--:--</strong>
      </div>
      <button id="checkAgainBtn" class="btn-check-again">
        <span>↻</span>
        <span id="txtCheckAgainBtn">Check again</span>
      </button>
    </section>

    <!-- 10. Technical Details (Accordion) -->
    <section class="tech-details-container">
      <button id="techDetailsToggle" class="tech-details-toggle">
        <span id="txtTechTitle">🔬 Technical details (Scientific)</span>
        <span id="techArrow" class="tech-arrow">▼</span>
      </button>
      <div id="techDetailsContent" class="tech-details-content">
        <div class="tech-grid">
          <div class="tech-item">
            <span id="txtTechNo2Label" class="tech-label">NO₂ Column</span>
            <span id="techNo2" class="tech-val">—</span>
            <span id="techNo2Obs" class="tech-sub">Sentinel-5P</span>
          </div>
          <div class="tech-item">
            <span id="txtTechSo2Label" class="tech-label">SO₂ Column</span>
            <span id="techSo2" class="tech-val">—</span>
            <span id="techSo2Obs" class="tech-sub">Sentinel-5P</span>
          </div>
          <div class="tech-item">
            <span id="txtTechWindLabel" class="tech-label">Wind (Speed & Direction)</span>
            <span id="techWind" class="tech-val">—</span>
            <span id="techWindDeg" class="tech-sub">Open-Meteo</span>
          </div>
          <div class="tech-item">
            <span id="txtTechTempLabel" class="tech-label">Temperature & Humidity</span>
            <span id="techTemp" class="tech-val">—</span>
            <span id="techHumidity" class="tech-sub">Surface sensor</span>
          </div>
        </div>
        <div class="tech-full-row">
          <strong id="txtTechGeeLabel">Satellite Status: </strong><span id="techGeeStatus">—</span>
        </div>
        <div class="tech-full-row">
          <strong id="txtTechObsLabel">Observation Time: </strong><span id="techObsTime">—</span>
        </div>
        <div class="tech-full-row">
          <strong id="txtTechCoordsLabel">Coordinates: </strong><span id="techCoords">—</span>
        </div>
      </div>
    </section>

    <!-- 11. Android Widget Mirror -->
    <section class="widget-preview-card">
      <div id="txtWidgetTitle" class="widget-preview-header">📱 Android Home-Screen Widget Preview</div>
      <div class="widget-box">
        <div class="widget-box-top">
          <span class="widget-box-title">VayuNet</span>
          <span id="widgetStatusText" class="widget-box-status" style="color: #10b981;">🟢 Air Good</span>
        </div>
        <div class="widget-box-metrics">
          <span id="widgetMovementText">Movement: SE</span>
          <span id="widgetUpdatedText">Updated: --:--</span>
        </div>
      </div>
    </section>

    <!-- 12. Alert Sound & Notification Button -->
    <button id="alertEnableBtn" class="alert-btn">
      <span>🔔</span>
      <span id="alertBtnLabel">Enable Alert Sound & Notifications</span>
    </button>

    <!-- 13. Scientific Disclaimer -->
    <p id="txtDisclaimer" class="disclaimer-text">Scientific Notice: VayuNet provides decision-support and awareness using satellite atmospheric columns and weather models. It does not replace official government pollution advisories.</p>
  </div>
  `;

  attachEventHandlers();
  initLeafletMap(currentLat, currentLon);
}

// In-place text updates for Language changes (NEVER re-creates #map!)
function applyLanguage() {
  document.querySelector("#txtAppTitle").textContent = t("appTitle");
  document.querySelector("#txtTagline").textContent = t("tagline");
  document.querySelector("#txtYourLocation").textContent = t("yourLocation");
  document.querySelector("#txtUpdateLocBtn").textContent = t("updateLocBtn");
  document.querySelector("#txtGpsTag").textContent = t("gpsDeviceLoc");
  document.querySelector("#txtWhyAlertTitle").textContent = t("whyAlertTitle");
  document.querySelector("#txtMapTitle").textContent = t("mapTitle");
  document.querySelector("#txtLegUser").textContent = t("legendUser");
  document.querySelector("#txtLegHotspot").textContent = t("legendHotspot");
  document.querySelector("#txtLegMove").textContent = t("legendMove");
  document.querySelector("#txtLegAffected").textContent = t("legendAffected");
  document.querySelector("#txtLegArrow").textContent = t("legendArrow");
  document.querySelector("#txtMoveTitle").textContent = t("movementTitle");
  document.querySelector("#txtAffTitle").textContent = t("affectedTitle");
  document.querySelector("#actionAlertLabel").textContent = t("whatToDoTitle");
  document.querySelector("#txtSitesTitle").textContent = t("prioritySitesTitle");
  document.querySelector("#txtLastUpdated").textContent = t("lastUpdated");
  document.querySelector("#txtCheckAgainBtn").textContent = t("checkAgainBtn");
  document.querySelector("#txtTechTitle").textContent = `🔬 ${t("techDetailsTitle")}`;
  document.querySelector("#txtTechNo2Label").textContent = t("no2Column");
  document.querySelector("#txtTechSo2Label").textContent = t("so2Column");
  document.querySelector("#txtTechWindLabel").textContent = t("windSpeedDir");
  document.querySelector("#txtTechTempLabel").textContent = t("tempHumidity");
  document.querySelector("#txtTechGeeLabel").textContent = `${t("geeStatus")}: `;
  document.querySelector("#txtTechObsLabel").textContent = `${t("obsTime")}: `;
  document.querySelector("#txtTechCoordsLabel").textContent = `${t("userCoords")}: `;
  document.querySelector("#txtWidgetTitle").textContent = `📱 ${t("widgetTitle")}`;
  document.querySelector("#txtReportBtn").textContent = t("reportBtn");
  document.querySelector("#txtReportTitle").textContent = t("reportTitle");
  document.querySelector("#txtReportSub").textContent = t("reportSub");
  document.querySelector("#txtCategoryLabel").textContent = t("categoryLabel");
  document.querySelector("#txtCatSmoke").textContent = t("catSmoke");
  document.querySelector("#txtCatFire").textContent = t("catFire");
  document.querySelector("#txtCatIndustrial").textContent = t("catIndustrial");
  document.querySelector("#txtCatDust").textContent = t("catDust");
  document.querySelector("#txtSubmitBtn").textContent = t("submitObservation");
  document.querySelector("#txtObsNotice").textContent = t("observationNotice");
  document.querySelector("#txtLegCitizen").textContent = t("legendCitizen");
  document.querySelector("#txtCitizenFeedTitle").textContent = t("citizenObsTitle");
  document.querySelector("#txtDisclaimer").textContent = t("disclaimer");

  const enBtn = document.querySelector("#langEnBtn");
  const taBtn = document.querySelector("#langTaBtn");
  if (enBtn && taBtn) {
    if (currentLang === "en") {
      enBtn.classList.add("active");
      taBtn.classList.remove("active");
    } else {
      taBtn.classList.add("active");
      enBtn.classList.remove("active");
    }
  }

  if (lastAnalysisData) {
    updateUI(lastAnalysisData);
  }
}

// Leaflet Map Initialization with CartoDB Voyager Tiles (OpenStreetMap Data, 100% Free, NO API KEY)
function initLeafletMap(lat, lon) {
  const container = document.getElementById("map");
  if (!container) return;

  const initialLat = lat || currentLat || 10.368;
  const initialLon = lon || currentLon || 77.980;

  if (map) {
    try {
      map.remove();
    } catch (e) {
      console.warn("Leaflet map cleanup notice:", e);
    }
    map = null;
  }

  try {
    map = L.map(container, {
      zoomControl: true,
      attributionControl: true
    }).setView([initialLat, initialLon], 11);

    // OpenStreetMap Humanitarian (HOT) tiles (100% Free, NO API KEY REQUIRED, crisp and clean)
    L.tileLayer("https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png", {
      subdomains: "abc",
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors, Tiles by <a href="https://www.hotosm.org/" target="_blank">Humanitarian OpenStreetMap Team</a>'
    }).addTo(map);

    // Initial user location marker
    if (lat && lon) {
      const userIcon = L.divIcon({
        className: "pulse-user-marker",
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      });
      userMarker = L.marker([lat, lon], { icon: userIcon, zIndexOffset: 1000 })
        .addTo(map)
        .bindPopup(`<b>🔵 ${t("legendUser")}</b>`);
    }

    requestAnimationFrame(() => {
      if (map) map.invalidateSize();
    });
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 200);
  } catch (err) {
    console.error("Leaflet initialization failed:", err);
  }
}

// Render All Layers on Map from Analysis Result
function renderMapData(data) {
  const uLat = data.user_location?.latitude ?? currentLat;
  const uLon = data.user_location?.longitude ?? currentLon;

  if (!uLat || !uLon) return;

  if (!map) {
    initLeafletMap(uLat, uLon);
  } else {
    map.invalidateSize();
  }

  // 1. User Marker (🔵 Blue = You / Current Location)
  if (userMarker) userMarker.remove();
  const userIcon = L.divIcon({
    className: "pulse-user-marker",
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
  const uPlace = data.user_location?.place_name || `${uLat.toFixed(4)}°, ${uLon.toFixed(4)}°`;
  userMarker = L.marker([uLat, uLon], { icon: userIcon })
    .addTo(map)
    .bindPopup(`<b>📍 ${t("legendUser")}</b><br>${uPlace}`);

  // 2. Clear previous dynamic layers
  if (hotspotMarker) { hotspotMarker.remove(); hotspotMarker = null; }
  if (movementArrowMarker) { movementArrowMarker.remove(); movementArrowMarker = null; }
  if (movementPathLayer) { movementPathLayer.remove(); movementPathLayer = null; }
  if (corridorLayer) { corridorLayer.remove(); corridorLayer = null; }
  if (affectedLayer) { affectedLayer.remove(); affectedLayer = null; }
  sensitiveMarkers.forEach(m => m.remove());
  sensitiveMarkers = [];

  const bounds = L.latLngBounds([[uLat, uLon]]);

  // Define exposure FIRST so expCenterLat and expCenterLon are always accessible without ReferenceError
  const exposure = data.exposure || data.potential_exposure;

  const hotspot = data.pollution_hotspot || data.hotspot;
  const hotspotDetected = hotspot && hotspot.detected === true && hotspot.latitude != null && hotspot.longitude != null;

  // 3. Pollution Hotspot Marker (🔴 Red = Pollution Hotspot, strictly separate from user)
  if (hotspotDetected) {
    const hLat = hotspot.latitude;
    const hLon = hotspot.longitude;
    bounds.extend([hLat, hLon]);

    const hotspotIcon = L.divIcon({
      className: "pulse-hotspot-marker",
      html: "⚠️",
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    const dist = hotspot.distance_from_user_km || hotspot.distance_km || 0;
    const pol = hotspot.pollutant || "NO₂";
    const hName = currentLang === "ta" ?
      (hotspot.name_ta || "மாசு மையம்") :
      (hotspot.name_en || "Pollution Hotspot");

    hotspotMarker = L.marker([hLat, hLon], { icon: hotspotIcon, zIndexOffset: 900 })
      .addTo(map)
      .bindPopup(`<b>🔴 ${hName}</b><br>Pollutant: <b>${pol}</b><br>Distance: <b>${dist} km from you</b>`);

    // 4. Movement Arrow & Directional Path (🌬️ Originating from pollution hotspot!)
    if (data.movement && data.movement.bearing_deg != null) {
      const brg = data.movement.bearing_deg;
      const dirLabel = currentLang === 'ta' ? data.movement.direction_ta : data.movement.direction;

      const expCenterLat = exposure?.center_latitude;
      const expCenterLon = exposure?.center_longitude;

      if (expCenterLat != null && expCenterLon != null) {
        bounds.extend([expCenterLat, expCenterLon]);
        movementPathLayer = L.polyline([[hLat, hLon], [expCenterLat, expCenterLon]], {
          color: "#ea580c",
          weight: 4,
          dashArray: "6, 6",
          opacity: 0.95
        }).addTo(map).bindPopup(`<b>🌬️ ${t("legendArrow")}:</b> ${dirLabel}`);
      }

      // High-visibility directional arrow marker (pointing along bearing_deg from North 0°)
      const arrowIcon = L.divIcon({
        className: "movement-arrow-marker",
        html: `
          <div style="width: 36px; height: 36px; transform: rotate(${brg}deg); filter: drop-shadow(0 2px 5px rgba(0,0,0,0.7));">
            <svg viewBox="0 0 36 36" width="36" height="36">
              <path d="M18 2 L30 16 L22 16 L22 34 L14 34 L14 16 L6 16 Z" fill="#ea580c" stroke="#ffffff" stroke-width="2.5" stroke-linejoin="round"/>
            </svg>
          </div>
        `,
        iconSize: [36, 36],
        iconAnchor: [18, 18]
      });

      // Position the arrow marker starting along the vector from the hotspot
      const arrowLat = expCenterLat != null ? (hLat * 0.65 + expCenterLat * 0.35) : hLat;
      const arrowLon = expCenterLon != null ? (hLon * 0.65 + expCenterLon * 0.35) : hLon;

      movementArrowMarker = L.marker([arrowLat, arrowLon], { icon: arrowIcon, zIndexOffset: 950 })
        .addTo(map)
        .bindPopup(`<b>🌬️ ${t("legendArrow")}:</b> ${dirLabel}`);
    }
  }

  // 5. 🟡 YELLOW: Potentially Affected Area (Broader dispersion polygon from Hotspot)
  if (exposure) {
    const affGeojson = exposure.affected_geojson || exposure.geojson;
    if (affGeojson) {
      affectedLayer = L.geoJSON(affGeojson, {
        style: {
          color: "#ca8a04",
          weight: 2,
          dashArray: "5, 5",
          fillColor: "#eab308",
          fillOpacity: 0.22
        }
      }).addTo(map);

      if (affGeojson.geometry && affGeojson.geometry.coordinates) {
        affGeojson.geometry.coordinates[0].forEach(coord => {
          bounds.extend([coord[1], coord[0]]);
        });
      }
    }

    // 6. 🟠 ORANGE: Possible Pollution Movement Corridor (Tighter plume corridor from Hotspot)
    const corrGeojson = exposure.corridor_geojson;
    if (corrGeojson) {
      corridorLayer = L.geoJSON(corrGeojson, {
        style: {
          color: "#ea580c",
          weight: 2.5,
          fillColor: "#f97316",
          fillOpacity: 0.38
        }
      }).addTo(map);

      if (corrGeojson.geometry && corrGeojson.geometry.coordinates) {
        corrGeojson.geometry.coordinates[0].forEach(coord => {
          bounds.extend([coord[1], coord[0]]);
        });
      }
    }
  }

  // 6b. Citizen Observations Layer (🟣 Purple camera pins)
  citizenMarkers.forEach(m => m.remove());
  citizenMarkers = [];

  if (data.citizen_observations && data.citizen_observations.length > 0) {
    data.citizen_observations.forEach(obs => {
      if (obs.latitude && obs.longitude) {
        bounds.extend([obs.latitude, obs.longitude]);
        const catLabel = currentLang === 'ta' ? (obs.category_label_ta || obs.category) : (obs.category_label_en || obs.category);
        const iconSymbol = obs.category_icon || "📸";
        const citIcon = L.divIcon({
          className: "pulse-citizen-marker",
          html: `<div class="citizen-marker-inner">${iconSymbol}</div>`,
          iconSize: [26, 26],
          iconAnchor: [13, 13]
        });

        const assessment = obs.ai_assessment || {};
        const assessHead = currentLang === 'ta' ? (assessment.headline_ta || assessment.headline_en) : assessment.headline_en;
        const distKm = obs.distance_km != null ? `${obs.distance_km} km away` : '';
        const timeStr = new Date(obs.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const photoHtml = obs.photo_preview ? `<div class="obs-popup-photo"><img src="${obs.photo_preview}" alt="${catLabel}" style="width:100%; max-height:120px; object-fit:cover; border-radius:6px; margin:4px 0;" /></div>` : '';

        const popupContent = `
          <div class="citizen-popup-wrap">
            <div class="obs-popup-header"><b>🟣 ${catLabel}</b> <small>(${distKm})</small></div>
            ${photoHtml}
            ${obs.description ? `<p class="obs-popup-desc">"${obs.description}"</p>` : ''}
            <div class="obs-popup-assessment">
              <span class="obs-pill">🔍 ${assessHead || t('groundVerificationReq')}</span>
            </div>
            <div class="obs-popup-footer"><small>📅 ${timeStr} • Citizen Evidence (Requires Verification)</small></div>
          </div>
        `;

        const cm = L.marker([obs.latitude, obs.longitude], { icon: citIcon, zIndexOffset: 850 })
          .addTo(map)
          .bindPopup(popupContent);
        citizenMarkers.push(cm);
      }
    });
  }

  // 7. Optional Priority Sites to Verify (Schools, Hospitals)
  if (data.sensitive_places && data.sensitive_places.length > 0) {
    data.sensitive_places.forEach(p => {
      if (p.latitude && p.longitude) {
        bounds.extend([p.latitude, p.longitude]);
        const sm = L.circleMarker([p.latitude, p.longitude], {
          radius: 7,
          color: "#c084fc",
          weight: 2,
          fillColor: "#7e22ce",
          fillOpacity: 0.85
        }).addTo(map).bindPopup(`<b>🟣 ${p.name}</b><br><small>${p.type} — ${t("prioritySitesTitle")}</small>`);
        sensitiveMarkers.push(sm);
      }
    });
  }

  // 8. Auto-fit bounds so BOTH user and hotspot/affected zone are visibly centered
  try {
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13, minZoom: 9 });
    } else {
      map.setView([uLat, uLon], 11);
    }
    setTimeout(() => { if (map) map.invalidateSize(); }, 200);
  } catch (e) {
    map.setView([uLat, uLon], 11);
  }
}

// Update UI with Analysis Result
function updateUI(d) {
  lastAnalysisData = d;
  const isTa = currentLang === "ta";

  // 1. Mode Badge
  const modeBadge = document.querySelector("#modeBadge");
  if (d.mode === "real") {
    modeBadge.textContent = t("realSatelliteBadge");
    modeBadge.className = "badge-mode real";
  } else {
    modeBadge.textContent = t("demoBadge");
    modeBadge.className = "badge-mode demo";
  }

  // 2. User Location Name & GPS Display
  const uLat = d.user_location?.latitude ?? currentLat;
  const uLon = d.user_location?.longitude ?? currentLon;
  const locName = d.user_location?.place_name || (uLat && uLon ? `${uLat.toFixed(4)}°N, ${uLon.toFixed(4)}°E` : "Device Location");
  document.querySelector("#locPlaceName").textContent = `📍 ${locName}`;
  if (uLat != null) document.querySelector("#locLatDisplay").textContent = `Latitude: ${uLat.toFixed(5)}`;
  if (uLon != null) document.querySelector("#locLonDisplay").textContent = `Longitude: ${uLon.toFixed(5)}`;

  // 3. Status Card (GREEN / ORANGE / RED)
  const risk = d.risk_level || d.status || "LOW";
  const heroCard = document.querySelector("#heroCard");
  const heroIcon = document.querySelector("#heroIcon");
  const heroTitle = document.querySelector("#heroTitle");
  const heroSub = document.querySelector("#heroSub");
  const actionCard = document.querySelector("#actionCard");
  const actionText = document.querySelector("#actionText");

  const cardData = d.status_card || {};
  const hotspot = d.pollution_hotspot || d.hotspot;
  const hotspotDetected = hotspot?.detected === true;
  const hasWind = d.weather?.wind_direction_deg != null && d.weather?.wind_speed_kmh != null;
  const userAffected = hasWind && d.exposure?.user_potentially_affected === true;

  if (hotspotDetected && userAffected) {
    // RED: Hotspot aligned with prevailing wind toward user
    heroCard.className = "hero-status-card HIGH";
    heroIcon.textContent = "🔴";
    heroTitle.textContent = isTa ? (cardData.title_ta || "கவனமாக இருக்கவும்") : (cardData.title_en || "ATTENTION");
    heroSub.textContent = isTa ?
      (cardData.summary_ta || "அருகில் உள்ள காற்று மாசு மையம், தற்போதைய காற்று வீசும் திசையால் உங்கள் பகுதியை நோக்கி நகர வாய்ப்புள்ளது. வரைபடத்தை பார்க்கவும்.") :
      (cardData.summary_en || "A nearby pollution hotspot is currently aligned with the prevailing wind toward your area. Consider checking the affected-area map.");
    actionCard.className = "action-card high-alert";
    actionText.textContent = isTa ? (cardData.action_ta || t("attentionAction")) : (cardData.action_en || t("attentionAction"));
  } else if (hotspotDetected && !hasWind) {
    // ORANGE: Hotspot detected, but wind data unavailable
    heroCard.className = "hero-status-card POLLUTED";
    heroIcon.textContent = "🟠";
    heroTitle.textContent = isTa ? (cardData.title_ta || "அருகில் காற்று மாசு உள்ளது") : (cardData.title_en || "POLLUTION NEARBY");
    heroSub.textContent = isTa ?
      (cardData.summary_ta || "அருகில் காற்று மாசு கண்டறியப்பட்டுள்ளது. காற்றின் தகவல் தற்போது கிடைக்காததால், நகர்வுப் பாதை தெரியவில்லை.") :
      (cardData.summary_en || "A pollution hotspot was detected nearby. Downwind analysis is unavailable as wind data cannot be determined.");
    actionCard.className = "action-card";
    actionText.textContent = isTa ? (cardData.action_ta || t("downwindUnavailableSub")) : (cardData.action_en || t("downwindUnavailableSub"));
  } else if (hotspotDetected && !userAffected) {
    // ORANGE: Hotspot detected nearby, but wind moving away
    heroCard.className = "hero-status-card POLLUTED";
    heroIcon.textContent = "🟠";
    heroTitle.textContent = isTa ? (cardData.title_ta || "அருகில் காற்று மாசு உள்ளது") : (cardData.title_en || "POLLUTION NEARBY");
    heroSub.textContent = isTa ?
      (cardData.summary_ta || "அருகில் காற்று மாசு கண்டறியப்பட்டுள்ளது. தற்போதைய காற்று உங்கள் பகுதியை நோக்கி வீசவில்லை.") :
      (cardData.summary_en || "A pollution hotspot was detected nearby. Current wind does not indicate movement toward your area.");
    actionCard.className = "action-card";
    actionText.textContent = isTa ? (cardData.action_ta || t("pollutionNearbyAction")) : (cardData.action_en || t("pollutionNearbyAction"));
  } else if (risk === "MODERATE") {
    heroCard.className = "hero-status-card CAREFUL";
    heroIcon.textContent = "🟡";
    heroTitle.textContent = isTa ? (cardData.title_ta || "கவனமாக இருக்கவும்") : (cardData.title_en || "BE CAREFUL");
    heroSub.textContent = isTa ? (cardData.summary_ta || "காற்று மாசு சற்று அதிகரித்துள்ளது.") : (cardData.summary_en || "Pollution is slightly elevated near your area.");
    actionCard.className = "action-card";
    actionText.textContent = isTa ? (cardData.action_ta || (hasWind ? t("pollutionNearbyAction") : t("downwindUnavailableSub"))) : (cardData.action_en || (hasWind ? t("pollutionNearbyAction") : t("downwindUnavailableSub")));
  } else {
    // GREEN: Clean atmosphere, no hotspot
    heroCard.className = "hero-status-card GOOD";
    heroIcon.textContent = "🟢";
    heroTitle.textContent = isTa ? (cardData.title_ta || "காற்று சுத்தமாக உள்ளது") : (cardData.title_en || "AIR IS GOOD");
    heroSub.textContent = isTa ? (cardData.summary_ta || "அருகில் குறிப்பிடத்தக்க காற்று மாசு மையம் எதுவும் இல்லை.") : (cardData.summary_en || "No significant nearby pollution hotspot detected.");
    actionCard.className = "action-card";
    actionText.textContent = isTa ? (cardData.action_ta || t("airGoodAction")) : (cardData.action_en || t("airGoodAction"));
  }

  // 4. WHY THIS ALERT?
  const whyText = isTa ?
    (d.why_this_alert?.ta || cardData.why_ta || t("whyAlertDefault")) :
    (d.why_this_alert?.en || cardData.why_en || t("whyAlertDefault"));
  document.querySelector("#whyAlertText").textContent = whyText;

  // 5. Movement Section
  const compass = document.querySelector("#movementCompass");
  const moveHeading = document.querySelector("#movementHeading");
  const moveSub = document.querySelector("#movementSub");

  if (hasWind && d.movement && d.movement.bearing_deg != null) {
    compass.textContent = "⬆️";
    compass.style.transform = `rotate(${d.movement.bearing_deg}deg)`;
    const dirStr = isTa ? d.movement.direction_ta : d.movement.direction;
    const shortDir = d.movement.direction_short || "";
    const speed = d.weather?.wind_speed_kmh;

    if (hotspotDetected) {
      moveHeading.textContent = `${t("movementFromHotspot")}: ${dirStr} (${shortDir})`;
    } else {
      moveHeading.textContent = `${t("windToward")}: ${dirStr} (${shortDir})`;
    }

    moveSub.textContent = speed != null ?
      (isTa ? `காற்றின் வேகம்: ${speed} கி.மீ/மணி` : `Surface wind speed: ${speed} km/h`) :
      (isTa ? "வானிலை தகவல் அடிப்படையில் கணிக்கப்பட்டது" : "Calculated from meteorological wind vectors");
  } else {
    compass.textContent = "🧭";
    compass.style.transform = "none";
    moveHeading.textContent = isTa ? "காற்றின் திசை கிடைக்கவில்லை" : t("weatherUnavailable");
    moveSub.textContent = isTa ? t("downwindUnavailableSub") : "Wind data is currently unavailable, so pollution movement and affected-area estimation cannot be determined.";
  }

  // 6. Potentially Affected Area Section
  const affIcon = document.querySelector("#affectedIcon");
  const affStatus = document.querySelector("#affectedStatus");
  const affSub = document.querySelector("#affectedSub");

  if (!hasWind || !d.exposure || d.exposure.downwind_available === false) {
    affIcon.textContent = "ℹ️";
    affStatus.textContent = t("downwindUnavailable");
    affSub.textContent = t("downwindUnavailableSub");
    affStatus.style.color = "#94a3b8";
  } else if (userAffected) {
    affIcon.textContent = "⚠️";
    affStatus.textContent = t("userMayBeAffected");
    affSub.textContent = isTa ? (d.exposure?.text_ta || "") : (d.exposure?.text_en || "");
    affStatus.style.color = "#fca5a5";
  } else {
    affIcon.textContent = "🛡️";
    affStatus.textContent = t("userNotAffected");
    affSub.textContent = isTa ? (d.exposure?.text_ta || "") : (d.exposure?.text_en || "");
    affStatus.style.color = "#f8fafc";
  }

  // 7. Map Render
  renderMapData(d);

  // 8. Sensitive Places List
  const sitesSection = document.querySelector("#sitesSection");
  const sitesList = document.querySelector("#sitesList");
  if (d.sensitive_places && d.sensitive_places.length > 0) {
    sitesSection.classList.remove("hidden");
    sitesList.innerHTML = d.sensitive_places.map(p => `
      <div class="site-item">
        <span class="site-name">${p.name}</span>
        <span class="site-badge">${p.type}</span>
      </div>
    `).join("");
  } else {
    sitesSection.classList.add("hidden");
  }

  // 9. Update Time
  const now = new Date();
  const timeFormatted = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  document.querySelector("#updateTimeDisplay").textContent = timeFormatted;

  // 10. Technical Details
  const no2Val = d.pollution?.no2 != null ? Number(d.pollution.no2).toExponential(2) : (d.satellite_available ? "0.00" : "Unavailable");
  const so2Val = d.pollution?.so2 != null ? Number(d.pollution.so2).toExponential(2) : (d.satellite_available ? "0.00" : "Unavailable");
  document.querySelector("#techNo2").textContent = no2Val;
  document.querySelector("#techNo2Obs").textContent = `${d.pollution?.no2_observations || 0} obs (7d)`;
  document.querySelector("#techSo2").textContent = so2Val;
  document.querySelector("#techSo2Obs").textContent = `${d.pollution?.so2_observations || 0} obs (7d)`;

  const wSpeed = d.weather?.wind_speed_kmh != null ? `${d.weather.wind_speed_kmh} km/h` : t("weatherUnavailable");
  const wDeg = d.weather?.wind_direction_deg != null ? `From ${d.weather.wind_direction_deg}°` : "";
  document.querySelector("#techWind").textContent = wSpeed;
  document.querySelector("#techWindDeg").textContent = wDeg;

  const tempVal = d.weather?.temperature_c != null ? `${d.weather.temperature_c}°C` : "—";
  const humidVal = d.weather?.humidity_pct != null ? `${d.weather.humidity_pct}% RH` : "";
  document.querySelector("#techTemp").textContent = tempVal;
  document.querySelector("#techHumidity").textContent = humidVal || "Atmosphere";

  document.querySelector("#techGeeStatus").textContent = d.satellite_available ?
    "Active (Sentinel-5P)" :
    (d.technical_details?.gee_diagnostic || t("satelliteUnavailable"));
  document.querySelector("#techObsTime").textContent = d.pollution?.no2_latest ?
    new Date(d.pollution.no2_latest).toLocaleString() : "Real-time weather proxy active";
  document.querySelector("#techCoords").textContent = `${d.user_location.latitude.toFixed(4)}°, ${d.user_location.longitude.toFixed(4)}°`;

  // 10b. Update Citizen Observations Feed
  const feedList = document.querySelector("#citizenFeedList");
  const feedBadge = document.querySelector("#citizenFeedBadge");
  const observations = d.citizen_observations || [];

  if (feedBadge) {
    feedBadge.textContent = `${observations.length} ${isTa ? 'பதிவுகள்' : 'REPORTS'}`;
  }

  if (feedList) {
    if (observations.length === 0) {
      feedList.innerHTML = `<div class="empty-feed-msg" id="txtNoCitizenObs">${t("noCitizenObs")}</div>`;
    } else {
      feedList.innerHTML = observations.map(obs => {
        const catLabel = isTa ? (obs.category_label_ta || obs.category) : (obs.category_label_en || obs.category);
        const icon = obs.category_icon || "📸";
        const dist = obs.distance_km != null ? `${obs.distance_km} km ${isTa ? 'தொலைவில்' : 'away'}` : '';
        const assessment = obs.ai_assessment || {};
        const assessHead = isTa ? (assessment.headline_ta || assessment.headline_en) : assessment.headline_en;
        const timeStr = new Date(obs.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        return `
          <div class="citizen-feed-item">
            ${obs.photo_preview ? `<div class="feed-item-thumb"><img src="${obs.photo_preview}" alt="${catLabel}" /></div>` : ''}
            <div class="feed-item-content">
              <div class="feed-item-top">
                <span class="feed-item-category">${icon} ${catLabel}</span>
                <span class="feed-item-dist">${dist}</span>
              </div>
              ${obs.description ? `<p class="feed-item-desc">"${obs.description}"</p>` : ''}
              <div>
                <span class="feed-item-pill">🔍 ${assessHead || t("groundVerificationReq")}</span>
              </div>
              <span class="feed-item-time">🕒 ${timeStr} • ${isTa ? 'கள ஆய்வு தேவை' : 'Citizen Evidence'}</span>
            </div>
          </div>
        `;
      }).join("");
    }
  }

  // 11. Android Widget Mirror
  const wStatus = document.querySelector("#widgetStatusText");
  const wMove = document.querySelector("#widgetMovementText");
  const wTime = document.querySelector("#widgetUpdatedText");

  if (hotspotDetected && userAffected) {
    wStatus.textContent = "🔴 High Risk";
    wStatus.style.color = "#ef4444";
  } else if (hotspotDetected) {
    wStatus.textContent = "🟠 Pollution Rising";
    wStatus.style.color = "#f97316";
  } else {
    wStatus.textContent = "🟢 Air Good";
    wStatus.style.color = "#10b981";
  }
  wMove.textContent = `Wind: ${d.movement?.direction_short || 'SE'}`;
  wTime.textContent = `Updated: ${timeFormatted}`;

  // 12. Alert Sound & Notification Trigger on High Risk
  if (d.alert && d.alert.should_alert) {
    playAlertSound(true);
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(isTa ? d.alert.title_ta : d.alert.title_en, {
        body: isTa ? d.alert.message_ta : d.alert.message_en,
        tag: "vayunet-risk-alert",
        icon: "/manifest.webmanifest"
      });
    }
  }
}

// Sound Synthesizer for Alerts
function playAlertSound(isSevere = false) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!audioContext) audioContext = new AudioCtx();
    if (audioContext.state === "suspended") audioContext.resume();

    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();

    osc.type = isSevere ? "sawtooth" : "sine";
    osc.frequency.setValueAtTime(isSevere ? 880 : 587.33, audioContext.currentTime);
    osc.frequency.exponentialRampToValueAtTime(isSevere ? 440 : 880, audioContext.currentTime + 0.35);

    gain.gain.setValueAtTime(0.2, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.35);

    osc.connect(gain);
    gain.connect(audioContext.destination);

    osc.start();
    osc.stop(audioContext.currentTime + 0.4);
  } catch (e) {
    console.debug("Audio error:", e);
  }

  if (navigator.vibrate) {
    if (isSevere) {
      navigator.vibrate([250, 100, 250, 100, 350]);
    } else {
      navigator.vibrate([180, 80, 180]);
    }
  }
}

// Request Notification Permission
async function requestNotifications() {
  playAlertSound(false);
  if ("Notification" in window) {
    const perm = await Notification.requestPermission();
    if (perm === "granted") {
      document.querySelector("#alertBtnLabel").textContent = t("alertBtnActive");
      new Notification("VayuNet", {
        body: t("tagline"),
        icon: "/manifest.webmanifest"
      });
      return;
    }
  }
  document.querySelector("#alertBtnLabel").textContent = t("alertBtnActive");
}

let isDemoOverride = null;

// Fetch Analysis from Backend
async function fetchAnalysis(lat, lon) {
  currentLat = lat;
  currentLon = lon;

  const modeBadge = document.querySelector("#modeBadge");
  modeBadge.textContent = t("checking");
  modeBadge.className = "badge-mode loading";

  document.querySelector("#heroTitle").textContent = t("loadingTitle");
  document.querySelector("#heroSub").textContent = t("loadingSub");
  document.querySelector("#whyAlertText").textContent = t("analyzing");

  const urlParams = new URLSearchParams(window.location.search);
  const demoParam = urlParams.get("demo");

  const payload = { latitude: lat, longitude: lon };
  if (demoParam !== null) {
    payload.demo = demoParam === "true";
  } else if (isDemoOverride !== null) {
    payload.demo = isDemoOverride;
  }

  try {
    const resp = await fetch(`${API_URL}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!resp.ok) {
      const errText = await resp.text();
      let errMsg = errText;
      try {
        const parsed = JSON.parse(errText);
        errMsg = parsed.detail || errText;
      } catch (e) {}

      modeBadge.textContent = "OFFLINE";
      modeBadge.className = "badge-mode demo";
      document.querySelector("#heroTitle").textContent = t("satelliteUnavailable");
      document.querySelector("#heroSub").textContent = t("loadingSub");
      return;
    }

    const data = await resp.json();
    updateUI(data);
  } catch (err) {
    console.warn("Backend fetch failed, attempting local fallback:", err);
    modeBadge.textContent = "OFFLINE";
    modeBadge.className = "badge-mode demo";
    document.querySelector("#heroTitle").textContent = t("satelliteUnavailable");
    document.querySelector("#heroSub").textContent = `Could not reach ${API_URL}. Ensure backend is running.`;
    document.querySelector("#whyAlertText").textContent = err.message;
  }
}

function onLocationSuccess(lat, lon, customCityName = null) {
  currentLat = lat;
  currentLon = lon;

  try {
    localStorage.setItem("vayunet_last_coords", JSON.stringify({ lat, lon }));
  } catch (e) {}

  const attachedGps = document.querySelector("#txtAttachedGps");
  if (attachedGps) {
    attachedGps.textContent = `📍 GPS Attached: ${lat.toFixed(5)}°, ${lon.toFixed(5)}°`;
  }

  const latDisplay = document.querySelector("#locLatDisplay");
  const lonDisplay = document.querySelector("#locLonDisplay");
  if (latDisplay) latDisplay.textContent = `Latitude: ${lat.toFixed(5)}`;
  if (lonDisplay) lonDisplay.textContent = `Longitude: ${lon.toFixed(5)}`;

  if (customCityName) {
    const placeNameEl = document.querySelector("#locPlaceName");
    if (placeNameEl) placeNameEl.textContent = `📍 ${customCityName}`;
  }

  if (map) {
    map.setView([lat, lon], 11);
    if (userMarker) userMarker.setLatLng([lat, lon]);
  } else {
    initLeafletMap(lat, lon);
  }

  fetchAnalysis(lat, lon);
}

// Acquire Device Geolocation (Strictly device GPS coordinates - no random IP fallback)
async function acquireLocation() {
  const placeNameEl = document.querySelector("#locPlaceName");
  if (placeNameEl) placeNameEl.textContent = `📍 ${t("gettingLoc")}`;

  // 1. URL Query Override (?lat=...&lon=...) e.g. when opened from Android Native App
  const urlParams = new URLSearchParams(window.location.search);
  const qLat = parseFloat(urlParams.get("lat"));
  const qLon = parseFloat(urlParams.get("lon"));
  if (!isNaN(qLat) && !isNaN(qLon) && qLat >= -90 && qLat <= 90 && qLon >= -180 && qLon <= 180 && (qLat !== 0 || qLon !== 0)) {
    onLocationSuccess(qLat, qLon, "Device GPS (Synced)");
    return;
  }

  // 2. Global Test Override
  if (window.__VAYUNET_LOCATION__) {
    onLocationSuccess(window.__VAYUNET_LOCATION__.latitude, window.__VAYUNET_LOCATION__.longitude);
    return;
  }

  // 3. Try HTML5 Geolocation API with high accuracy GPS
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180 && (lat !== 0 || lon !== 0)) {
          onLocationSuccess(lat, lon);
        } else if (placeNameEl) {
          placeNameEl.textContent = "📍 Invalid coordinates received from device. Tap 'Update my location' to retry.";
        }
      },
      err => {
        console.warn("Device geolocation notice:", err.message);
        if (placeNameEl) {
          placeNameEl.textContent = "📍 Unable to get your current location. Please allow location access, enable GPS, and tap 'Update my location'.";
        }
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  } else {
    if (placeNameEl) {
      placeNameEl.textContent = "📍 Geolocation is not supported by your browser.";
    }
  }
}

// Attach UI Event Handlers
function attachEventHandlers() {
  // Mode Badge Click Toggle (switch between DEMO and REAL mode)
  document.querySelector("#modeBadge")?.addEventListener("click", () => {
    isDemoOverride = isDemoOverride === null ? false : !isDemoOverride;
    if (currentLat && currentLon) fetchAnalysis(currentLat, currentLon);
  });

  // Language Switch: updates text in-place WITHOUT re-creating #map!
  document.querySelector("#langEnBtn")?.addEventListener("click", () => {
    currentLang = "en";
    localStorage.setItem("vayunet_lang", "en");
    applyLanguage();
  });

  document.querySelector("#langTaBtn")?.addEventListener("click", () => {
    currentLang = "ta";
    localStorage.setItem("vayunet_lang", "ta");
    applyLanguage();
  });

  // Refresh Button
  document.querySelector("#refreshBtn")?.addEventListener("click", () => {
    const btn = document.querySelector("#refreshBtn");
    btn.style.transform = "rotate(360deg)";
    setTimeout(() => { btn.style.transform = ""; }, 500);
    acquireLocation();
  });

  // Check Again Button
  document.querySelector("#checkAgainBtn")?.addEventListener("click", () => {
    acquireLocation();
  });

  // Update Location Button
  document.querySelector("#locateMeBtn")?.addEventListener("click", () => {
    acquireLocation();
  });

  // Technical Details Toggle (Accordion)
  document.querySelector("#techDetailsToggle")?.addEventListener("click", () => {
    const content = document.querySelector("#techDetailsContent");
    const arrow = document.querySelector("#techArrow");
    if (content.classList.contains("open")) {
      content.classList.remove("open");
      arrow.textContent = "▼";
    } else {
      content.classList.add("open");
      arrow.textContent = "▲";
    }
  });

  // Notification Button
  document.querySelector("#alertEnableBtn")?.addEventListener("click", requestNotifications);

  // --- Citizen Observation Handlers ---
  const reportSection = document.querySelector("#citizenReportSection");
  const openReportBtn = document.querySelector("#btnOpenCitizenReport");
  const closeReportBtn = document.querySelector("#btnCloseCitizenReport");
  const photoDropArea = document.querySelector("#photoDropArea");
  const photoInput = document.querySelector("#citizenPhotoInput");
  const photoPreviewWrap = document.querySelector("#photoPreviewWrap");
  const photoPreviewImg = document.querySelector("#citizenPhotoPreview");
  const removePhotoBtn = document.querySelector("#btnRemovePhoto");
  const submitReportBtn = document.querySelector("#btnSubmitCitizenReport");
  const descTextarea = document.querySelector("#citizenDescription");
  const assessmentCard = document.querySelector("#assessmentResultCard");
  const assessmentHeadline = document.querySelector("#assessmentResultHeadline");
  const assessmentBody = document.querySelector("#assessmentResultBody");

  // Toggle report section
  openReportBtn?.addEventListener("click", () => {
    reportSection?.classList.toggle("hidden");
    if (!reportSection?.classList.contains("hidden")) {
      reportSection?.scrollIntoView({ behavior: "smooth", block: "start" });
      const attachedGps = document.querySelector("#txtAttachedGps");
      if (attachedGps && currentLat && currentLon) {
        attachedGps.textContent = `📍 GPS Attached: ${currentLat.toFixed(5)}°, ${currentLon.toFixed(5)}°`;
      }
    }
  });

  closeReportBtn?.addEventListener("click", () => {
    reportSection?.classList.add("hidden");
  });

  // Photo Input Triggers
  photoDropArea?.addEventListener("click", () => {
    photoInput?.click();
  });

  // Handle Image Selection with Client Compression to max 800px
  photoInput?.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const maxDim = 800;
        let w = img.width;
        let h = img.height;
        if (w > h && w > maxDim) {
          h = Math.round((h * maxDim) / w);
          w = maxDim;
        } else if (h > maxDim) {
          w = Math.round((w * maxDim) / h);
          h = maxDim;
        }
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, w, h);
        currentPhotoBase64 = canvas.toDataURL("image/jpeg", 0.78);

        if (photoPreviewImg) photoPreviewImg.src = currentPhotoBase64;
        photoDropArea?.classList.add("hidden");
        photoPreviewWrap?.classList.remove("hidden");
        if (submitReportBtn) submitReportBtn.disabled = false;
      };
      img.src = event.target.result;
    };
    reader.readAsDataURL(file);
  });

  removePhotoBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    currentPhotoBase64 = null;
    if (photoInput) photoInput.value = "";
    photoPreviewWrap?.classList.add("hidden");
    photoDropArea?.classList.remove("hidden");
    if (submitReportBtn) submitReportBtn.disabled = true;
  });

  // Category Selection
  document.querySelectorAll(".category-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".category-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      selectedCitizenCategory = chip.getAttribute("data-cat") || "smoke_haze";
    });
  });

  // Submit Observation
  submitReportBtn?.addEventListener("click", async () => {
    if (!currentPhotoBase64) {
      alert("Please take or select a photo of the visible pollution first.");
      return;
    }
    const lat = currentLat;
    const lon = currentLon;
    if (!lat || !lon) {
      alert("Device location is still being detected. Please wait for GPS coordinates.");
      return;
    }

    submitReportBtn.disabled = true;
    submitReportBtn.textContent = t("submitting");

    try {
      const resp = await fetch(`${API_URL}/api/observations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          latitude: lat,
          longitude: lon,
          photo_base64: currentPhotoBase64,
          category: selectedCitizenCategory,
          description: descTextarea?.value || ""
        })
      });

      if (resp.ok) {
        const result = await resp.json();
        const obs = result.observation || {};
        const assessment = obs.ai_assessment || {};

        // Show assessment result
        if (assessmentCard && assessmentHeadline && assessmentBody) {
          assessmentHeadline.textContent = `🔍 ${assessment.headline_en || "AI Visual Assessment"}`;
          assessmentBody.textContent = `${assessment.assessment_en || "Recorded as citizen ground evidence."} (${assessment.disclaimer || ""})`;
          assessmentCard.classList.remove("hidden");
        }

        // Reset form
        currentPhotoBase64 = null;
        if (photoInput) photoInput.value = "";
        photoPreviewWrap?.classList.add("hidden");
        photoDropArea?.classList.remove("hidden");
        if (descTextarea) descTextarea.value = "";

        submitReportBtn.textContent = "✓ Observation Submitted!";
        setTimeout(() => {
          submitReportBtn.textContent = t("submitObservation");
          submitReportBtn.disabled = true;
        }, 3000);

        // Refresh analysis to reflect new citizen observation layer
        fetchAnalysis(lat, lon);
      } else {
        alert("Failed to submit observation. Please check network connection.");
        submitReportBtn.disabled = false;
        submitReportBtn.textContent = t("submitObservation");
      }
    } catch (err) {
      console.error("Citizen observation submit error:", err);
      alert(`Submission error: ${err.message}`);
      submitReportBtn.disabled = false;
      submitReportBtn.textContent = t("submitObservation");
    }
  });

  // Check URL param action=report (e.g. from Android app)
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("action") === "report") {
    reportSection?.classList.remove("hidden");
    reportSection?.scrollIntoView({ behavior: "smooth" });
  }
}

// Bootstrapping
createDOMShellOnce();
acquireLocation();

// Auto-refresh every 5 minutes
setInterval(() => {
  if (currentLat && currentLon) fetchAnalysis(currentLat, currentLon);
}, 300000);

// Register PWA Service Worker for Offline Caching & "Add to Home Screen"
if ("serviceWorker" in navigator && (window.location.protocol === "https:" || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js")
      .then(reg => console.debug("VayuNet PWA Service Worker registered:", reg.scope))
      .catch(err => console.debug("Service Worker notice:", err));
  });
}

