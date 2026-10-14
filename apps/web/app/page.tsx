"use client";

import { useEffect, useState, useRef, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { 
  getHealth, createCase, uploadDocument, processDocument, getCase, getCaseFacts, getFactEvidence, translateCase, API_BASE,
  logoutUser, getMe, getUserCases,
  type CaseOut, type FactResponse, type EvidenceResponse, type TranslatedText, type UserProfile
} from "@/lib/api";
import { 
  registerWithFirebase, loginWithFirebase, logoutFirebase,
  onAuthStateChange, saveUserCaseToFirestore, getUserCasesFromFirestore,
  saveUserProfileToFirestore, getMasterUserData, logUserActivity,
  type UserProfileData, type UserActivityItem
} from "@/lib/firebase";
import { 
  FileUp, Loader2, Calendar, Pill, AlertTriangle, FileText, 
  X, Printer, Globe, ShieldAlert, Sparkles, Clock, Stethoscope, HeartHandshake,
  ChevronRight, Activity, AlertCircle, ShieldCheck, PhoneCall, Check, ExternalLink, Lock,
  User, LogOut, Key, Mail, Play, Pause, Square, Volume2, CheckCircle2, Languages
} from "lucide-react";

export type Lang = "en" | "hi" | "gu" | "mr" | "ta" | "te";

export const UI_I18N: Record<Lang, {
  printPlan: string;
  readAloud: string;
  pause: string;
  resume: string;
  stop: string;
  newEncounter: string;
  attachedFiles: string;
  reviewAlertsTitle: string;
  reviewAlertsDesc: string;
  goToReview: string;
  cautionConflict: string;
  cautionMissingEvidence: string;
  emergencyWarnings: string;
  emergencySub: string;
  viewSourceProof: string;
  followups: string;
  followupsEmpty: string;
  prescriptions: string;
  prescriptionsEmpty: string;
  homeCare: string;
  homeCareEmpty: string;
  instructionsLabel: string;
  warnings_title: string;
  appointments_title: string;
  medications_title: string;
  instructions_title: string;
  allergies_title: string;
  dates_title: string;
}> = {
  en: {
    printPlan: "Print Plan",
    readAloud: "Read Aloud",
    pause: "Pause",
    resume: "Resume",
    stop: "Stop",
    newEncounter: "New Encounter",
    attachedFiles: "Attached Files:",
    reviewAlertsTitle: "Clinical Safety & Document Review Alerts",
    reviewAlertsDesc: "Issues were flagged across your paperwork that require clinician or patient confirmation. CARELYNX does not guess ambiguous facts.",
    goToReview: "Open Review Queue →",
    cautionConflict: "Caution: Conflict",
    cautionMissingEvidence: "Caution: Missing Evidence",
    emergencyWarnings: "Emergency Warning Signs & Red Flags",
    emergencySub: "Seek immediate medical care if you experience any of the following",
    viewSourceProof: "View Source Proof →",
    followups: "Follow-up Appointments",
    followupsEmpty: "No follow-up dates extracted from uploaded pages.",
    prescriptions: "Prescribed Medications",
    prescriptionsEmpty: "No discharge prescriptions identified.",
    homeCare: "Home Care & Daily Instructions",
    homeCareEmpty: "No specific home instructions extracted.",
    instructionsLabel: "Instructions:",
    warnings_title: "Emergency Warning Signs",
    appointments_title: "Follow-up Appointments",
    medications_title: "Prescribed Medications",
    instructions_title: "Care Instructions",
    allergies_title: "Documented Allergies",
    dates_title: "Hospital Stay Dates",
  },
  hi: {
    printPlan: "योजना प्रिंट करें",
    readAloud: "बोलकर सुनाएं",
    pause: "रोकें",
    resume: "फिर से चलाएं",
    stop: "बंद करें",
    newEncounter: "नया मरीज़ दस्तावेज़",
    attachedFiles: "संलग्न फ़ाइलें:",
    reviewAlertsTitle: "चिकित्सीय सुरक्षा व समीक्षा चेतावनियां",
    reviewAlertsDesc: "आपके दस्तावेज़ों में ऐसे बिंदु मिले हैं जिनकी डॉक्टर से पुष्टि आवश्यक है। CARELYNX किसी भी विरोधाभास का अनुमान नहीं लगाता।",
    goToReview: "समीक्षा सूची खोलें →",
    cautionConflict: "सावधानी: विरोधाभास",
    cautionMissingEvidence: "सावधानी: साक्ष्य अनुपलब्ध",
    emergencyWarnings: "आपातकालीन चेतावनी संकेत व खतरे के लक्षण",
    emergencySub: "यदि आपको इनमें से कोई भी लक्षण महसूस हो तो तुरंत आपातकालीन चिकित्सा सहायता लें",
    viewSourceProof: "मूल प्रमाण देखें →",
    followups: "आगामी डॉक्टर से मिलने का समय",
    followupsEmpty: "अपलोड किए गए पृष्ठों में से कोई आगामी तारीख नहीं मिली।",
    prescriptions: "निर्धारित दवाइयां",
    prescriptionsEmpty: "डिस्चार्ज के समय कोई दवाई दर्ज नहीं है।",
    homeCare: "घर पर देखभाल व दैनिक निर्देश",
    homeCareEmpty: "कोई विशिष्ट घरेलू निर्देश नहीं मिले।",
    instructionsLabel: "निर्देश:",
    warnings_title: "आपातकालीन चेतावनी संकेत",
    appointments_title: "आगामी मिलने का समय",
    medications_title: "निर्धारित दवाइयां",
    instructions_title: "देखभाल निर्देश",
    allergies_title: "दर्ज की गई एलर्जी",
    dates_title: "अस्पताल में भर्ती व छुट्टी की तारीखें",
  },
  gu: {
    printPlan: "યોજના પ્રિન્ટ કરો",
    readAloud: "મોટેથી વાંચો",
    pause: "અટકાવો",
    resume: "ફરીથી ચલાવો",
    stop: "બંધ કરો",
    newEncounter: "નવો દર્દી દસ્તાવેજ",
    attachedFiles: "જોડાયેલ ફાઇલો:",
    reviewAlertsTitle: "તબીબી સલામતી અને સમીક્ષા ચેતવણીઓ",
    reviewAlertsDesc: "તમારા કાગળોમાં એવી બાબતો નોંધાઈ છે જેની તબીબી ખાતરી જરૂરી છે.",
    goToReview: "સમીક્ષા કતાર ખોલો →",
    cautionConflict: "સાવધાની: વિરોધાભાસ",
    cautionMissingEvidence: "સાવધાની: પુરાવો ખૂટે છે",
    emergencyWarnings: "કટોકટી ચેતવણી ચિહ્નો અને રેડ ફ્લેગ્સ",
    emergencySub: "જો તમને આમાંથી કોઈપણ લક્ષણ જણાય તો તાત્કાલિક તબીબી સારવાર મેળવો",
    viewSourceProof: "મૂળ પુરાવો જુઓ →",
    followups: "તબીબી મુલાકાતો",
    followupsEmpty: "અપલોડ કરેલા પૃષ્ઠોમાંથી કોઈ તારીખ મળી નથી.",
    prescriptions: "સૂચવેલ દવાઓ",
    prescriptionsEmpty: "ડિસ્ચાર્જ દવાઓ મળી નથી.",
    homeCare: "ઘરેલું સંભાળ અને દૈનિક સૂચનાઓ",
    homeCareEmpty: "કોઈ ચોક્કસ સૂચનાઓ મળી નથી.",
    instructionsLabel: "સૂચનાઓ:",
    warnings_title: "કટોકટી ચેતવણી ચિહ્નો",
    appointments_title: "તબીબી મુલાકાતો",
    medications_title: "સૂચવેલ દવાઓ",
    instructions_title: "સંભાળ સૂચનાઓ",
    allergies_title: "નોંધાયેલ એલર્જી",
    dates_title: "હોસ્પિટલ રોકાણની તારીખો",
  },
  mr: {
    printPlan: "योजना मुद्रित करा",
    readAloud: "मोठ्याने वाचा",
    pause: "थांबवा",
    resume: "पुन्हा सुरू करा",
    stop: "बंद करा",
    newEncounter: "नवीन रुग्ण नोंदणी",
    attachedFiles: "संलग्न फायली:",
    reviewAlertsTitle: "वैद्यकीय सुरक्षा आणि पुनरावलोकन सूचना",
    reviewAlertsDesc: "आपल्या कागदपत्रांमध्ये अशा बाबी आढळल्या आहेत ज्यांची डॉक्टरांकडून पुष्टी आवश्यक आहे.",
    goToReview: "पुनरावलोकन रांग उघडा →",
    cautionConflict: "सावधान: विसंगती",
    cautionMissingEvidence: "सावधान: पुरावा उपलब्ध नाही",
    emergencyWarnings: "तातडीचे चेतावणी संकेत व धोक्याची लक्षणे",
    emergencySub: "यापैकी कोणतेही लक्षण आढळल्यास त्वरित वैद्यकीय मदत घ्या",
    viewSourceProof: "मूळ पुरावा पहा →",
    followups: "पुढील तपासणीच्या वेळा",
    followupsEmpty: "अपलोड केलेल्या पानांवरून कोणतीही तारीख सापडली नाही.",
    prescriptions: "दिलेली औषधे",
    prescriptionsEmpty: "डिस्चार्ज औषधे सापडली नाहीत.",
    homeCare: "घरातील काळजी व दैनंदिन सूचना",
    homeCareEmpty: "कोणत्याही विशिष्ट सूचना सापडल्या नाहीत.",
    instructionsLabel: "सूचना:",
    warnings_title: "तातडीचे चेतावणी संकेत",
    appointments_title: "पुढील तपासणीच्या वेळा",
    medications_title: "दिलेली औषधे",
    instructions_title: "काळजीच्या सूचना",
    allergies_title: "नोंदवलेली ऍलर्जी",
    dates_title: "रुग्णालयातील मुक्कामाच्या तारखा",
  },
  ta: {
    printPlan: "திட்டத்தை அச்சிடுக",
    readAloud: "சத்தமாக வாசிக்கவும்",
    pause: "இடைநிறுத்து",
    resume: "மீண்டும் தொடங்கு",
    stop: "நிறுத்து",
    newEncounter: "புதிய நோயாளி ஆவணம்",
    attachedFiles: "இணைக்கப்பட்ட கோப்புகள்:",
    reviewAlertsTitle: "மருத்துவ பாதுகாப்பு மற்றும் மறுஆய்வு எச்சரிக்கைகள்",
    reviewAlertsDesc: "உங்கள் ஆவணங்களில் மருத்துவர் உறுதிப்படுத்த வேண்டிய முரண்பாடுகள் உள்ளன.",
    goToReview: "மறுஆய்வு வரிசையைத் திறக்கவும் →",
    cautionConflict: "எச்சரிக்கை: முரண்பாடு",
    cautionMissingEvidence: "எச்சரிக்கை: சான்று இல்லை",
    emergencyWarnings: "அவசர எச்சரிக்கை அறிகுறிகள்",
    emergencySub: "பின்வருவனவற்றில் ஏதேனும் ஏற்பட்டால் உடனடியாக மருத்துவ உதவியை நாடுங்கள்",
    viewSourceProof: "அசல் ஆதாரத்தைப் பார்க்கவும் →",
    followups: "அடுத்த மருத்துவ சந்திப்புகள்",
    followupsEmpty: "பதிவேற்றிய பக்கங்களில் இருந்து தேதிகள் எதுவும் பெறப்படவில்லை.",
    prescriptions: "பரிந்துரைக்கப்பட்ட மருந்துகள்",
    prescriptionsEmpty: "மருந்துகள் எதுவும் குறிப்பிடப்படவில்லை.",
    homeCare: "வீட்டு பராமரிப்பு மற்றும் அன்றாட வழிமுறைகள்",
    homeCareEmpty: "குறிப்பிட்ட வழிமுறைகள் எதுவும் இல்லை.",
    instructionsLabel: "வழிமுறைகள்:",
    warnings_title: "அவசர எச்சரிக்கை அறிகுறிகள்",
    appointments_title: "அடுத்த சந்திப்புகள்",
    medications_title: "மருந்துகள்",
    instructions_title: "பராமரிப்பு வழிமுறைகள்",
    allergies_title: "பதிவு செய்யப்பட்ட ஒவ்வாமைகள்",
    dates_title: "மருத்துவமனை தங்கிய நாட்கள்",
  },
  te: {
    printPlan: "ప్లాన్ ప్రింట్ చేయండి",
    readAloud: "బిగ్గరగా చదవండి",
    pause: "విరామం",
    resume: "పునఃప్రారంభించు",
    stop: "ఆపివేయి",
    newEncounter: "కొత్త రోగి రికార్డు",
    attachedFiles: "జతచేయబడిన ఫైళ్లు:",
    reviewAlertsTitle: "వైద్య భద్రత మరియు సమీక్ష హెచ్చరికలు",
    reviewAlertsDesc: "మీ పత్రాలలో డాక్టర్ ధృవీకరణ అవసరమైన అంశాలు గుర్తించబడ్డాయి.",
    goToReview: "సమీక్ష క్యూను తెరవండి →",
    cautionConflict: "హెచ్చరిక: వైరుధ్యం",
    cautionMissingEvidence: "హెచ్చరిక: రుజువు లేదు",
    emergencyWarnings: "అత్యవసర హెచ్చరిక సంకేతాలు",
    emergencySub: "కింది వాటిలో ఏవైనా కనిపిస్తే వెంటనే వైద్య సహాయం పొందండి",
    viewSourceProof: "అసలు రుజువు చూడండి →",
    followups: "తదుపరి అపాయింట్‌మెంట్లు",
    followupsEmpty: "అప్‌లోڈ చేసిన పేజీల నుండి తదుపరి తేదీలు కనుగొనబడలేదు.",
    prescriptions: "సూచించిన మందులు",
    prescriptionsEmpty: "డిశ్చార్జ్ మందులు గుర్తించబడలేదు.",
    homeCare: "ఇంటి సంరక్షణ & రోజువారీ సూచనలు",
    homeCareEmpty: "ఎటువంటి ప్రత్యేక సూచనలు లేవు.",
    instructionsLabel: "సూచనలు:",
    warnings_title: "అత్యవసర హెచ్చరిక సంకేతాలు",
    appointments_title: "తదుపరి అపాయింట్‌మెంట్లు",
    medications_title: "సూచించిన మందులు",
    instructions_title: "సంరక్షణ సూచనలు",
    allergies_title: "నమోదిత అలర్జీలు",
    dates_title: "ఆసుపత్రి బస తేదీలు",
  },
};

function HomeContent() {
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [activeCase, setActiveCase] = useState<CaseOut | null>(null);
  const [facts, setFacts] = useState<FactResponse[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Translation state
  const [language, setLanguage] = useState<Lang>("en");
  const [isTranslating, setIsTranslating] = useState(false);
  const [translations, setTranslations] = useState<Record<string, TranslatedText>>({});
  const ui = UI_I18N[language] || UI_I18N.en;
  
  // Evidence popup state
  const [selectedFact, setSelectedFact] = useState<FactResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidenceResponse[]>([]);
  const [isFetchingEvidence, setIsFetchingEvidence] = useState(false);

  // Helpline copy feedback state
  const [helplineCopied, setHelplineCopied] = useState(false);
  
  // Pre-upload consent gateway state
  const [showUploadConsentModal, setShowUploadConsentModal] = useState(false);
  const [consentAge, setConsentAge] = useState(false);
  const [consentPrivacy, setConsentPrivacy] = useState(false);
  const [hasSessionUploadConsent, setHasSessionUploadConsent] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  // User Account & History state (Strict Tenant/User Isolation)
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authName, setAuthName] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
  const [userCases, setUserCases] = useState<CaseOut[]>([]);
  const [loadingCases, setLoadingCases] = useState(false);
  const [ttsState, setTtsState] = useState<"idle" | "playing" | "paused">("idle");

  // Patient Profile Modal state (Stored in single table 'user_data')
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileData, setProfileData] = useState<UserProfileData>({
    displayName: "",
    email: "",
    phone: "",
    dob: "",
    emergencyContactName: "",
    emergencyContactPhone: "",
    bloodGroup: "",
    preferredLanguage: "en",
    updatedAt: ""
  });
  const [profileActivities, setProfileActivities] = useState<UserActivityItem[]>([]);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileSuccessMsg, setProfileSuccessMsg] = useState<string | null>(null);
  const [profileErrorMsg, setProfileErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const speechQueueRef = useRef<string[]>([]);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const isSpeechStoppedRef = useRef<boolean>(false);
  const [mobileTab, setMobileTab] = useState<"all" | "warnings" | "followups" | "meds" | "instructions">("all");

  useEffect(() => {
    getHealth().catch((e: Error) => setError(e.message));

    const unsubscribe = onAuthStateChange(async (firebaseUser) => {
      if (firebaseUser) {
        try {
          const token = await firebaseUser.getIdToken();
          if (typeof window !== "undefined") {
            localStorage.setItem("carelynx_auth_token", token);
          }
        } catch {
          // non-blocking
        }
        setCurrentUser({
          id: firebaseUser.uid,
          email: firebaseUser.email || "patient@carelynx.local",
          full_name: firebaseUser.displayName || null,
          role: "patient",
          created_at: firebaseUser.metadata?.creationTime || new Date().toISOString()
        });

        // Restore single-time consent if this user has already consented
        if (typeof window !== "undefined") {
          const hasConsent = localStorage.getItem(`carelynx_consent_accepted_${firebaseUser.uid}`) === "true";
          if (hasConsent) {
            setHasSessionUploadConsent(true);
            setConsentAge(true);
            setConsentPrivacy(true);
          }
        }
      } else {
        getMe()
          .then(setCurrentUser)
          .catch(() => setCurrentUser(null));
      }
    });

    return () => {
      unsubscribe();
      isSpeechStoppedRef.current = true;
      speechQueueRef.current = [];
      currentUtteranceRef.current = null;
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handledActionRef = useRef<string | null>(null);

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthLoading(true);
    try {
      let uid = "";
      if (authMode === "register") {
        const fbUser = await registerWithFirebase(authEmail, authPassword, authName || undefined);
        const token = await fbUser.getIdToken();
        if (typeof window !== "undefined") {
          localStorage.setItem("carelynx_auth_token", token);
        }
        uid = fbUser.uid;
        setCurrentUser({
          id: fbUser.uid,
          email: fbUser.email || authEmail,
          full_name: authName || fbUser.displayName || null,
          role: "patient",
          created_at: new Date().toISOString()
        });
      } else {
        const fbUser = await loginWithFirebase(authEmail, authPassword);
        const token = await fbUser.getIdToken();
        if (typeof window !== "undefined") {
          localStorage.setItem("carelynx_auth_token", token);
        }
        uid = fbUser.uid;
        setCurrentUser({
          id: fbUser.uid,
          email: fbUser.email || authEmail,
          full_name: fbUser.displayName || null,
          role: "patient",
          created_at: new Date().toISOString()
        });
      }

      // Check single-time consent for this user
      if (typeof window !== "undefined" && uid) {
        const hasConsent = localStorage.getItem(`carelynx_consent_accepted_${uid}`) === "true";
        if (hasConsent) {
          setHasSessionUploadConsent(true);
          setConsentAge(true);
          setConsentPrivacy(true);
        }
      }

      setShowAuthModal(false);
      setAuthPassword("");
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setAuthLoading(false);
    }
  };


  const handleLogout = async () => {
    try {
      await logoutFirebase();
    } catch {
      // ignore
    }
    logoutUser();
    setCurrentUser(null);
    setUserCases([]);
    setShowHistoryDrawer(false);
    setHasSessionUploadConsent(false);
    setConsentAge(false);
    setConsentPrivacy(false);
  };

  const handleOpenProfile = useCallback(async () => {
    if (!currentUser) {
      setShowAuthModal(true);
      return;
    }
    setShowProfileModal(true);
    setProfileLoading(true);
    setProfileSuccessMsg(null);
    setProfileErrorMsg(null);
    try {
      const master = await getMasterUserData(currentUser.id);
      setProfileData({
        displayName: master.profile?.displayName || currentUser.full_name || "",
        email: master.profile?.email || currentUser.email || "",
        phone: master.profile?.phone || "",
        dob: master.profile?.dob || "",
        emergencyContactName: master.profile?.emergencyContactName || "",
        emergencyContactPhone: master.profile?.emergencyContactPhone || "",
        bloodGroup: master.profile?.bloodGroup || "Unknown",
        preferredLanguage: master.profile?.preferredLanguage || language || "en",
        updatedAt: master.profile?.updatedAt || ""
      });
      setProfileActivities(master.activities || []);
    } catch (err) {
      console.warn("Could not load profile from Firestore:", err);
    } finally {
      setProfileLoading(false);
    }
  }, [currentUser, language]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;
    setProfileSaving(true);
    setProfileSuccessMsg(null);
    setProfileErrorMsg(null);
    try {
      const saved = await saveUserProfileToFirestore(currentUser.id, profileData);
      setProfileData(saved);
      setCurrentUser(prev => prev ? { ...prev, full_name: saved.displayName } : null);
      if (saved.preferredLanguage && saved.preferredLanguage !== language) {
        handleLanguageChange(saved.preferredLanguage as Lang);
      }
      setProfileSuccessMsg("Profile details saved successfully");
      const updatedMaster = await getMasterUserData(currentUser.id);
      setProfileActivities(updatedMaster.activities || []);
    } catch (err) {
      setProfileErrorMsg(err instanceof Error ? err.message : "Failed to save profile details");
    } finally {
      setProfileSaving(false);
    }
  };

  const handleOpenHistory = useCallback(async () => {
    if (!currentUser) {
      setShowAuthModal(true);
      return;
    }
    setShowHistoryDrawer(true);
    setLoadingCases(true);
    try {
      // 1. Fetch case memories strictly for this user from Cloud Firestore single table
      const firestoreRecords = await getUserCasesFromFirestore(currentUser.id);
      const userCaseIdSet = new Set(firestoreRecords.map(f => f.case_id));

      // 2. Fetch backend local cases ONLY if they belong to this user
      let backendCases: CaseOut[] = [];
      try {
        const allBackendCases = await getUserCases();
        backendCases = allBackendCases.filter(b => userCaseIdSet.has(b.id));
      } catch (e) {
        console.warn("Backend cases fetch fallback:", e);
      }

      // 3. Build strictly isolated list of cases for this user only
      const backendMap = new Map<string, CaseOut>(backendCases.map(b => [b.id, b]));
      const isolatedCases: CaseOut[] = firestoreRecords.map(f => {
        const existingBackend = backendMap.get(f.case_id);
        if (existingBackend) {
          return {
            ...existingBackend,
            created_at: f.created_at || existingBackend.created_at,
          };
        }
        return {
          id: f.case_id,
          status: f.status,
          created_at: f.created_at,
          documents: [{
            id: f.case_id,
            filename: f.filename,
            processing_status: f.status,
          }],
          counts: {
            verified: f.facts_count?.total || 0,
            needs_review: 0,
            human_required: 0,
            conflict_detected: 0,
            rejected: 0,
            open_reviews: 0
          }
        };
      });

      setUserCases(isolatedCases);
      logUserActivity(currentUser.id, "VIEWED_HISTORY", "Viewed personal case history", { case_count: isolatedCases.length });
    } catch (err) {
      console.error("Failed to load user cases from Firestore:", err);
    } finally {
      setLoadingCases(false);
    }
  }, [currentUser]);

  const handleSelectHistoryCase = async (c: CaseOut) => {
    try {
      setIsProcessing(true);
      setShowHistoryDrawer(false);
      const [fullCase, caseFacts] = await Promise.all([getCase(c.id), getCaseFacts(c.id)]);
      setActiveCase(fullCase);
      setFacts(caseFacts);

      const openAlertCount = caseFacts.filter(
        item => item.status === "NEEDS_REVIEW" || 
                item.status === "CONFLICT_DETECTED" || 
                item.status === "HUMAN_REQUIRED"
      ).length;

      if (typeof window !== "undefined") {
        localStorage.setItem("carelynx_recent_case_id", c.id);
        if (currentUser) {
          localStorage.setItem(`carelynx_recent_case_${currentUser.id}`, c.id);
        }
        window.dispatchEvent(new CustomEvent("carelynx:active-alerts", { detail: { count: openAlertCount } }));
      }

      setTimeout(() => {
        const el = document.getElementById("care-plan");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 300);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load selected case");
    } finally {
      setIsProcessing(false);
    }
  };

  // Common upload pipeline
  const uploadAndProcessFile = useCallback(async (file: File) => {
    try {
      setIsUploading(true);
      setError(null);
      
      const newCase = await createCase();
      const caseId = newCase.id;
      
      const doc = await uploadDocument(caseId, file);
      await processDocument(doc.id);
      
      const [c, f] = await Promise.all([getCase(caseId), getCaseFacts(caseId)]);
      setActiveCase(c);
      setFacts(f);
      setIsProcessing(false);

      const openAlertCount = f.filter(
        item => item.status === "NEEDS_REVIEW" || 
                item.status === "CONFLICT_DETECTED" || 
                item.status === "HUMAN_REQUIRED"
      ).length;

      if (typeof window !== "undefined") {
        localStorage.setItem("carelynx_recent_case_id", caseId);
        if (currentUser) {
          localStorage.setItem(`carelynx_recent_case_${currentUser.id}`, caseId);
        }
        window.dispatchEvent(new CustomEvent("carelynx:active-alerts", { detail: { count: openAlertCount } }));
      }

      if (currentUser) {
        try {
          await saveUserCaseToFirestore(currentUser.id, {
            caseId,
            title: file.name.replace(/\.[^/.]+$/, ""),
            filename: file.name,
            status: "PROCESSED",
            documentCount: 1,
            factsCount: {
              total: f.length,
              medications: f.filter(item => item.fact_type === "medication").length,
              appointments: f.filter(item => item.fact_type === "follow_up").length,
              warnings: f.filter(item => item.fact_type === "warning_sign").length,
              instructions: f.filter(item => item.fact_type === "instruction" || item.fact_type === "documented_condition").length
            }
          });
          await logUserActivity(
            currentUser.id,
            "UPLOADED_PAPERWORK",
            `Uploaded and extracted discharge document: ${file.name}`,
            { case_id: caseId, alerts_count: openAlertCount }
          );
        } catch (fsErr) {
          console.warn("Could not sync case memory to Firestore:", fsErr);
        }
      }

      if (language !== "en") {
        setIsTranslating(true);
        try {
          const res = await translateCase(caseId, language);
          setTranslations(res);
        } catch (err) {
          console.error("Auto-translation on upload failed:", err);
        } finally {
          setIsTranslating(false);
        }
      }

      setTimeout(() => {
        const el = document.getElementById("care-plan");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 300);
      
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }, [language, currentUser]);

  // 1-Click Sample Hospital PDF loader
  const handleLoadSample = useCallback(async (
    samplePath: string = "/sample_medical_record.pdf", 
    filename: string = "sample_discharge_summary.pdf",
    targetSection?: string
  ) => {
    if (!currentUser) {
      setAuthError("Please sign in or create an account to explore clinical paperwork.");
      setShowAuthModal(true);
      return;
    }
    try {
      setIsUploading(true);
      setError(null);
      const res = await fetch(samplePath);
      const blob = await res.blob();
      const file = new File([blob], filename, { type: "application/pdf" });
      await uploadAndProcessFile(file);
      
      if (targetSection) {
        setTimeout(() => {
          const el = document.getElementById(targetSection);
          if (el) el.scrollIntoView({ behavior: "smooth" });
        }, 800);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load sample document");
      setIsUploading(false);
    }
  }, [uploadAndProcessFile, currentUser]);

  // Handle custom events and URL parameters from Navbar / external links
  useEffect(() => {
    const handleUploadEvent = () => {
      if (hasSessionUploadConsent) {
        fileInputRef.current?.click();
      } else {
        setShowUploadConsentModal(true);
      }
    };

    const handleHomeEvent = () => {
      if (activeCase) {
        setActiveCase(null);
        setFacts([]);
        if (typeof window !== "undefined") {
          localStorage.removeItem("carelynx_recent_case_id");
          if (currentUser) {
            localStorage.removeItem(`carelynx_recent_case_${currentUser.id}`);
          }
          window.dispatchEvent(new CustomEvent("carelynx:active-alerts", { detail: { count: 0 } }));
        }
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    };

    const handleFeaturesEvent = () => {
      if (activeCase) {
        setActiveCase(null);
        setFacts([]);
        setTimeout(() => {
          const el = document.getElementById("features");
          if (el) el.scrollIntoView({ behavior: "smooth" });
        }, 120);
      } else {
        const el = document.getElementById("features");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }
    };

    const handleCarePlanEvent = () => {
      if (activeCase) {
        const el = document.getElementById("care-plan");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      } else {
        handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "care-plan");
      }
    };

    const handlePrescriptionsEvent = () => {
      if (activeCase) {
        const el = document.getElementById("prescriptions");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      } else {
        handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "prescriptions");
      }
    };

    const handleHistoryEvent = () => {
      handleOpenHistory();
    };

    const handleProfileEvent = () => {
      handleOpenProfile();
    };

    window.addEventListener("carelynx:upload", handleUploadEvent);
    window.addEventListener("carelynx:home", handleHomeEvent);
    window.addEventListener("carelynx:features", handleFeaturesEvent);
    window.addEventListener("carelynx:careplan", handleCarePlanEvent);
    window.addEventListener("carelynx:prescriptions", handlePrescriptionsEvent);
    window.addEventListener("carelynx:history", handleHistoryEvent);
    window.addEventListener("carelynx:profile", handleProfileEvent);

    // Check URL params — once per action: this effect re-runs on every case update, and re-running
    // "demo" would upload the sample again in a loop.
    const action = searchParams.get("action");
    const isNewAction = action !== handledActionRef.current;
    handledActionRef.current = action;
    if (isNewAction && action) {
      setTimeout(() => {
        if (action === "upload") {
          if (hasSessionUploadConsent) {
            fileInputRef.current?.click();
          } else {
            setShowUploadConsentModal(true);
          }
        } else if (action === "history") {
          handleHistoryEvent();
        } else if (action === "profile") {
          handleProfileEvent();
        } else if (action === "demo") {
          handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "care-plan");
        } else if (action === "prescriptions") {
          handlePrescriptionsEvent();
        } else if (action === "care-plan") {
          handleCarePlanEvent();
        } else if (action === "features") {
          handleFeaturesEvent();
        } else if (action === "home") {
          handleHomeEvent();
        }
      }, 0);
    }

    return () => {
      window.removeEventListener("carelynx:upload", handleUploadEvent);
      window.removeEventListener("carelynx:home", handleHomeEvent);
      window.removeEventListener("carelynx:features", handleFeaturesEvent);
      window.removeEventListener("carelynx:careplan", handleCarePlanEvent);
      window.removeEventListener("carelynx:prescriptions", handlePrescriptionsEvent);
      window.removeEventListener("carelynx:history", handleHistoryEvent);
      window.removeEventListener("carelynx:profile", handleProfileEvent);
    };
  }, [activeCase, handleLoadSample, hasSessionUploadConsent, searchParams, currentUser, handleOpenHistory, handleOpenProfile]);

  // Close popup modal on ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (showUploadConsentModal) setShowUploadConsentModal(false);
        if (selectedFact) setSelectedFact(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedFact, showUploadConsentModal]);

  // Poll for case status during background processing
  useEffect(() => {
    if (!activeCase || !isProcessing) return;
    
    const interval = setInterval(async () => {
      try {
        const c = await getCase(activeCase.id);
        setActiveCase(c);
        
        const isStillProcessing = c.documents.some(
          d => d.processing_status === "PROCESSING" || d.processing_status === "UPLOADED"
        );
        
        if (!isStillProcessing) {
          setIsProcessing(false);
          const f = await getCaseFacts(c.id);
          setFacts(f);

          const openAlertCount = f.filter(
            item => item.status === "NEEDS_REVIEW" || 
                    item.status === "CONFLICT_DETECTED" || 
                    item.status === "HUMAN_REQUIRED"
          ).length;

          if (typeof window !== "undefined") {
            window.dispatchEvent(new CustomEvent("carelynx:active-alerts", { detail: { count: openAlertCount } }));
          }

          // Auto-translate summary upon completion if a non-English language is active
          if (language !== "en") {
            setIsTranslating(true);
            try {
              setTranslations(await translateCase(c.id, language));
            } catch (err) {
              console.error("Auto-translation on summary creation failed:", err);
            } finally {
              setIsTranslating(false);
            }
          }
        }
      } catch (err) {
        console.error(err);
      }
    }, 1200);
    
    return () => clearInterval(interval);
  }, [activeCase, isProcessing, language]);

  // Handle multilingual translation
  const handleLanguageChange = async (targetLang: "en" | "hi" | "gu" | "mr" | "ta" | "te") => {
    if (!currentUser) {
      setAuthError("Please sign in or create an account to translate clinical paperwork.");
      setShowAuthModal(true);
      return;
    }
    if (targetLang === "en") {
      setLanguage("en");
      return;
    }
    if (!activeCase) {
      await handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf");
      setLanguage(targetLang);
      return;
    }
    
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setTtsState("idle");

    setIsTranslating(true);
    try {
      setTranslations(await translateCase(activeCase.id, targetLang));
      setLanguage(targetLang);
    } catch (err) {
      console.error(err);
    } finally {
      setIsTranslating(false);
    }
  };

  // Break long discharge instructions into conversational chunks (<140 chars) to prevent Chromium TTS freeze
  const splitIntoSpeechChunks = (text: string, maxLen = 140): string[] => {
    const rawSentences = text
      .split(/(?<=[.?!;:\n])\s+/)
      .map(s => s.trim())
      .filter(Boolean);
    
    const chunks: string[] = [];
    for (const sent of rawSentences) {
      if (sent.length <= maxLen) {
        chunks.push(sent);
      } else {
        const words = sent.split(" ");
        let currentChunk = "";
        for (const w of words) {
          if ((currentChunk + " " + w).trim().length <= maxLen) {
            currentChunk = (currentChunk + " " + w).trim();
          } else {
            if (currentChunk) chunks.push(currentChunk);
            currentChunk = w;
          }
        }
        if (currentChunk) chunks.push(currentChunk);
      }
    }
    return chunks;
  };

  const handleStopReadAloud = () => {
    isSpeechStoppedRef.current = true;
    speechQueueRef.current = [];
    currentUtteranceRef.current = null;
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setTtsState("idle");
  };

  const playNextSpeechChunk = (synth: SpeechSynthesis, bcp47: string, voice?: SpeechSynthesisVoice) => {
    if (isSpeechStoppedRef.current || speechQueueRef.current.length === 0) {
      setTtsState("idle");
      currentUtteranceRef.current = null;
      return;
    }

    const nextChunk = speechQueueRef.current.shift();
    if (!nextChunk) {
      setTtsState("idle");
      currentUtteranceRef.current = null;
      return;
    }

    try {
      const utt = new SpeechSynthesisUtterance(nextChunk);
      currentUtteranceRef.current = utt; // Critical: prevents Chromium V8 garbage collection mid-speech

      if (voice) {
        utt.voice = voice;
        utt.lang = voice.lang || bcp47;
      } else {
        utt.lang = bcp47;
      }
      utt.rate = 0.95;

      utt.onend = () => {
        if (!isSpeechStoppedRef.current) {
          playNextSpeechChunk(synth, bcp47, voice);
        }
      };

      utt.onerror = (e) => {
        console.warn("Speech chunk error or interrupted:", e);
        if (!isSpeechStoppedRef.current) {
          playNextSpeechChunk(synth, bcp47, voice);
        }
      };

      synth.speak(utt);
      if (synth.paused) {
        synth.resume();
      }
    } catch (err) {
      console.warn("Error playing speech chunk:", err);
      setTtsState("idle");
    }
  };

  const handleToggleReadAloud = () => {
    if (!currentUser) {
      setAuthError("Please sign in or create an account to use the Read Aloud accessibility feature.");
      setShowAuthModal(true);
      return;
    }
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Speech synthesis is not supported by your browser.");
      return;
    }
    const synth = window.speechSynthesis;

    if (ttsState === "playing") {
      synth.pause();
      setTtsState("paused");
      return;
    }
    if (ttsState === "paused") {
      synth.resume();
      setTtsState("playing");
      return;
    }

    // Starting new playback
    handleStopReadAloud();
    isSpeechStoppedRef.current = false;

    const bcp47 = SPEECH_LANG[language] || "en-IN";
    const voices = synth.getVoices() || [];
    const prefix = bcp47.split("-")[0].toLowerCase();

    // Multi-stage voice matching with universal fallback
    let voice = voices.find(v => v.lang.replace("_", "-").toLowerCase() === bcp47.toLowerCase());
    if (!voice) voice = voices.find(v => v.lang.replace("_", "-").toLowerCase().startsWith(prefix));
    if (!voice) {
      const langNames: Record<string, string> = { en: "english", hi: "hindi", gu: "gujarati", mr: "marathi", ta: "tamil", te: "telugu" };
      const keyword = langNames[language];
      if (keyword) voice = voices.find(v => v.name.toLowerCase().includes(keyword));
    }
    if (!voice && language !== "en") {
      // Graceful fallback to Indian locale or any available voice
      voice = voices.find(v => v.lang.toLowerCase().includes("in")) || voices[0];
    }
    if (!voice && voices.length > 0) {
      voice = voices[0];
    }

    const intro = READ_ALOUD_INTRO[language] || READ_ALOUD_INTRO.en;
    // CRITICAL: Read ALL points extracted from paperwork (not just VERIFIED)
    const allClinicalFacts = facts.filter(f => f.status !== "REJECTED");
    if (allClinicalFacts.length === 0) {
      alert("No discharge points available to read.");
      return;
    }

    const sectionsText: string[] = [intro];

    // 1. Emergency Warning Signs & Red Flags
    const wFacts = allClinicalFacts.filter(f => f.fact_type === "warning_sign");
    if (wFacts.length > 0) {
      const wItems = wFacts.map(f => {
        const tr = translations[f.id];
        const val = f.value || {};
        const title = tr?.title || val.text || getFactTitle(f);
        const meaning = tr?.subtitle || val.simplified_meaning || val.meaning;
        return meaning ? `${title}. ${meaning}` : `${title}`;
      }).join(". ");
      sectionsText.push(`${UI_I18N[language]?.warnings_title || "Emergency Warning Signs"}: ${wItems}`);
    }

    // 2. Follow-Up Appointments
    const apptFacts = allClinicalFacts.filter(f => f.fact_type === "follow_up");
    if (apptFacts.length > 0) {
      const apptItems = apptFacts.map(f => {
        const tr = translations[f.id];
        const val = f.value || {};
        const title = tr?.title || getFactTitle(f);
        const date = tr?.date || val.date;
        const meaning = tr?.subtitle || val.simplified_meaning;
        let line = title;
        if (date) line += ` on ${date}`;
        if (meaning) line += `. ${meaning}`;
        return line;
      }).join(". ");
      sectionsText.push(`${UI_I18N[language]?.appointments_title || "Follow-up Appointments"}: ${apptItems}`);
    }

    // 3. Prescribed Medications
    const medFacts = allClinicalFacts.filter(f => f.fact_type === "medication");
    if (medFacts.length > 0) {
      const medItems = medFacts.map(f => {
        const tr = translations[f.id];
        const val = f.value || {};
        const name = String(tr?.title || val.name || getFactTitle(f));
        const strength = val.strength ? String(val.strength) : "";
        const freq = tr?.subtitle || (val.frequency ? String(val.frequency) : "");
        const meaning = val.simplified_meaning ? String(val.simplified_meaning) : "";
        let line = name;
        if (strength) line += ` ${strength}`;
        if (freq) line += `, ${freq}`;
        if (meaning) line += `. ${meaning}`;
        return line;
      }).join(". ");
      sectionsText.push(`${UI_I18N[language]?.medications_title || "Prescribed Medications"}: ${medItems}`);
    }

    // 4. Care Instructions & Documented Conditions
    const instFacts = allClinicalFacts.filter(f => f.fact_type === "instruction" || f.fact_type === "documented_condition");
    if (instFacts.length > 0) {
      const instItems = instFacts.map(f => {
        const tr = translations[f.id];
        const val = f.value || {};
        const title = tr?.title || val.text || val.raw_text || getFactTitle(f);
        const meaning = tr?.subtitle || val.simplified_meaning;
        return meaning ? `${title}. ${meaning}` : `${title}`;
      }).join(". ");
      sectionsText.push(`${UI_I18N[language]?.instructions_title || "Care Instructions"}: ${instItems}`);
    }

    // 5. Documented Allergies
    const allergyFacts = allClinicalFacts.filter(f => f.fact_type === "allergy");
    if (allergyFacts.length > 0) {
      const allergyItems = allergyFacts.map(f => {
        const val = f.value || {};
        if (val.no_known_allergies) return "No known drug allergies";
        return `Allergic to ${val.substance || "unspecified substance"}`;
      }).join(". ");
      sectionsText.push(`${UI_I18N[language]?.allergies_title || "Documented Allergies"}: ${allergyItems}`);
    }

    // 6. Hospital Encounter Dates
    const dateFacts = allClinicalFacts.filter(f => f.fact_type === "encounter_date");
    if (dateFacts.length > 0) {
      const dateItems = dateFacts.map(f => {
        const val = f.value || {};
        const kind = val.kind === "admission" ? "Hospital Admission" : val.kind === "discharge" ? "Hospital Discharge" : "Encounter";
        return `${kind} on ${val.date || val.raw_text}`;
      }).join(". ");
      sectionsText.push(`${UI_I18N[language]?.dates_title || "Hospital Stay Dates"}: ${dateItems}`);
    }

    const fullText = sectionsText.join(". ");
    const chunks = splitIntoSpeechChunks(fullText, 140);
    if (chunks.length === 0) {
      setTtsState("idle");
      return;
    }

    speechQueueRef.current = chunks;
    setTtsState("playing");
    playNextSpeechChunk(synth, bcp47, voice);
  };


  // Upload custom file with consent gateway check
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!currentUser) {
      setAuthError("Please sign in or create an account to upload paperwork.");
      setShowAuthModal(true);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    if (!hasSessionUploadConsent) {
      setPendingFile(file);
      setShowUploadConsentModal(true);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    await uploadAndProcessFile(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const initiateUploadClick = () => {
    if (!currentUser) {
      setAuthError("Please sign in or create an account to upload paperwork.");
      setShowAuthModal(true);
      return;
    }
    if (hasSessionUploadConsent) {
      fileInputRef.current?.click();
    } else {
      setShowUploadConsentModal(true);
    }
  };

  const handleConfirmUploadConsent = async () => {
    if (!consentAge || !consentPrivacy) return;
    setHasSessionUploadConsent(true);
    setShowUploadConsentModal(false);

    // Persist single-time consent for logged-in user so they are never asked again
    if (currentUser?.id) {
      try {
        localStorage.setItem(`carelynx_consent_accepted_${currentUser.id}`, "true");
        logUserActivity(currentUser.id, "PATIENT_CONSENT_ACCEPTED", "Confirmed patient paperwork privacy & clinical navigation consent.");
      } catch {
        // non-blocking
      }
    }

    if (pendingFile) {
      const f = pendingFile;
      setPendingFile(null);
      await uploadAndProcessFile(f);
    } else {
      fileInputRef.current?.click();
    }
  };

  const copyHelplineNumber = () => {
    navigator.clipboard.writeText("1800-CARELYNX");
    setHelplineCopied(true);
    setTimeout(() => setHelplineCopied(false), 2500);
  };
  
  const viewEvidence = async (fact: FactResponse) => {
    if (!currentUser) {
      setAuthError("Please sign in or create an account to inspect verbatim evidence.");
      setShowAuthModal(true);
      return;
    }
    setSelectedFact(fact);
    setIsFetchingEvidence(true);
    setEvidence([]);
    try {
      const ev = await getFactEvidence(fact.id);
      setEvidence(ev);
    } catch (err) {
      console.error(err);
    } finally {
      setIsFetchingEvidence(false);
    }
  };

  const getFactTitle = (fact: FactResponse): string => {
    const tr = language !== "en" ? translations[fact.id] : undefined;
    if (tr) return [tr.title, tr.subtitle, tr.date].filter(Boolean).join(" — ");
    const val = fact.value || {};
    const sanitize = (s: string) => s.replace(/^["'“”„\s:.-]+|["'“”„\s:.-]+$/g, "").trim();

    switch (fact.fact_type) {
      case "encounter_date": {
        const kind = String(val.kind || "");
        const kindLabel = kind === "admission" ? "Hospital Admission" : kind === "discharge" ? "Hospital Discharge" : "Encounter";
        const dateStr = String(val.date || val.raw_text || "");
        return `${kindLabel}: ${dateStr}`;
      }
      case "follow_up": {
        const raw = sanitize(String(val.raw_text || ""));
        const date = String(val.date || "");
        const provider = sanitize(String(val.provider || ""));
        const dept = sanitize(String(val.department || ""));
        if (dept && provider) return `${dept} Follow-up with ${provider}`;
        if (provider) return `Follow-up with ${provider}`;
        if (dept) return `${dept} Follow-up`;
        if (date) return `Follow-up Visit (${date})`;
        return raw || "Scheduled Follow-up Appointment";
      }
      case "medication": {
        const name = sanitize(String(val.name || "Medication"));
        const strength = val.strength ? sanitize(String(val.strength)) : "";
        const freq = val.frequency ? sanitize(String(val.frequency)) : "";
        const details = [strength, freq].filter(Boolean).join(" • ");
        return `${name} ${details ? "— " + details : ""}`;
      }
      case "warning_sign": return sanitize(String(val.text || "Warning sign"));
      case "documented_condition": return sanitize(String(val.text || "Condition"));
      case "allergy": return `Allergy: ${sanitize(String(val.substance || "Substance"))}`;
      case "instruction": return sanitize(String(val.text || "Care Instruction"));
      default: return sanitize(String(fact.fact_type));
    }
  };

  // Categorize facts
  const warnings = facts.filter(f => f.fact_type === "warning_sign" && f.status !== "REJECTED");
  const medications = facts.filter(f => f.fact_type === "medication" && f.status !== "REJECTED");
  const appointments = facts.filter(f => f.fact_type === "follow_up" && f.status !== "REJECTED");
  const instructions = facts.filter(f => (f.fact_type === "instruction" || f.fact_type === "documented_condition" || f.fact_type === "encounter_date") && f.status !== "REJECTED");

  return (
    <div className="flex-1 w-full max-w-[1720px] mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8 flex flex-col gap-8 sm:gap-12">
      {/* Global Error Banner */}
      {error && (
        <div className="p-4 border border-rose-200 bg-rose-50 text-rose-800 rounded-2xl text-sm flex items-start gap-3 shadow-xs no-print fade-in">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-rose-900">Processing Notification</p>
            <p className="text-xs text-rose-700 mt-0.5">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 p-1 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Persistent hidden file input for paperwork upload across all views */}
      <input 
        type="file" 
        className="hidden" 
        onChange={handleFileUpload}
        disabled={isUploading || isProcessing}
        ref={fileInputRef}
        accept="application/pdf,image/jpeg,image/png"
      />

      {/* Main View: Landing Hero OR Active Case Care Plan */}
      {!activeCase ? (
        <div className="flex flex-col gap-16" id="hero">
          {/* Hero Section */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center pt-4 sm:pt-8 pb-4">
            {/* Left Hero Content */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              <div>
                {/* User Session Banner (Isolated Medical History) */}
                <div className="mb-4">
                  {currentUser ? (
                    <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800 shadow-xs">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span>Private Patient: <strong>{currentUser.email}</strong></span>
                      <button 
                        onClick={handleOpenHistory}
                        className="ml-1 text-emerald-700 underline font-bold hover:text-emerald-900 cursor-pointer"
                        id="hero-view-history"
                      >
                        My Cases
                      </button>
                      <button 
                        onClick={handleLogout}
                        className="ml-2 text-slate-400 hover:text-rose-600 cursor-pointer"
                        title="Sign Out"
                        aria-label="Sign Out"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowAuthModal(true)}
                      className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 border border-slate-200 text-xs font-semibold text-slate-700 transition-colors cursor-pointer"
                      id="hero-signin-badge"
                    >
                      <User className="w-3.5 h-3.5 text-slate-600" />
                      <span>Sign In / Register to isolate & save your private medical records</span>
                    </button>
                  )}
                </div>

                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 leading-[1.15]">
                  A clear, evidence-linked <br className="hidden sm:inline" />
                  <span className="text-brand font-extrabold">discharge companion</span> <br className="hidden sm:inline" />
                  for every patient
                </h1>
                <p className="mt-5 text-slate-600 text-base sm:text-lg leading-relaxed max-w-xl">
                  Supporting your post-hospital recovery with AI-guided fact extraction, verified medication schedules, clinical warnings, and safe multilingual translation. 100% grounded in source paperwork.
                </p>
              </div>

              {/* Action Buttons Group */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                {/* 1. Royal Blue Button */}
                <button
                  onClick={initiateUploadClick}
                  disabled={isUploading || isProcessing}
                  className="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold text-sm shadow-md shadow-blue-500/20 transition-all flex items-center gap-2 cursor-pointer focus-visible:outline-2 focus-visible:outline-blue-600 focus-visible:outline-offset-2"
                  id="hero-btn-upload"
                  aria-label="Upload patient paperwork"
                >
                  {isUploading ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <FileUp className="w-4 h-4" aria-hidden="true" />}
                  <span>Upload Paperwork</span>
                </button>

                {/* 2. Vibrant Mint Green Button */}
                <button
                  onClick={() => handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "care-plan")}
                  disabled={isUploading || isProcessing}
                  className="px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-bold text-sm shadow-md shadow-emerald-500/20 transition-all flex items-center gap-2 cursor-pointer"
                  id="hero-btn-demo"
                >
                  {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  <span>Demo Hospital Report</span>
                </button>

                {/* 3. Soft Sky Button with Deep Navy Contrast */}
                <button
                  onClick={() => handleLoadSample("/sample_conflicting_prescription.pdf", "sample_conflicting_prescription.pdf")}
                  disabled={isUploading || isProcessing}
                  className="px-5 py-3.5 rounded-xl bg-sky-100 hover:bg-sky-200 text-sky-950 font-bold text-sm border border-sky-300 transition-all flex items-center gap-2 shadow-xs cursor-pointer"
                  id="hero-btn-conflict"
                >
                  <AlertTriangle className="w-4 h-4 text-sky-800" />
                  <span>Test Conflict</span>
                </button>

                {/* 4. Emergency Crimson Button */}
                <a
                  href="/review"
                  className="px-5 py-3.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-sm shadow-md shadow-rose-500/20 transition-all flex items-center gap-2 cursor-pointer"
                  id="hero-btn-emergency"
                >
                  <ShieldAlert className="w-4 h-4" />
                  <span>Clinical Queue</span>
                </a>
              </div>

              {/* Interactive 24/7 Helpline Pill */}
              <div className="pt-2 flex items-center gap-3">
                <a
                  href="tel:1800227359"
                  onClick={(e) => {
                    if (!("ontouchstart" in window)) {
                      e.preventDefault();
                      copyHelplineNumber();
                    }
                  }}
                  className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-white/95 border border-slate-300 text-xs text-slate-800 shadow-xs hover:border-emerald-500 transition-colors backdrop-blur-md group cursor-pointer"
                  title="Click to call or copy helpline number"
                >
                  <span className="w-2 h-2 rounded-full bg-rose-600 animate-pulse shrink-0" />
                  <span className="font-bold text-slate-900 flex items-center gap-1.5">
                    <PhoneCall className="w-3.5 h-3.5 text-rose-600" />
                    Carelynx Patient Helpline:
                  </span>
                  <span className="font-mono text-slate-700 font-semibold">1800-CARELYNX</span>
                  <span className="text-[11px] text-brand font-semibold hidden sm:inline">
                    {helplineCopied ? "✓ Copied!" : "(24/7 Support)"}
                  </span>
                </a>
              </div>
            </div>

            {/* Right Hero Feature Showcase Card */}
            <div className="lg:col-span-5 flex justify-center">
              <div className="w-full max-w-md bg-gradient-to-br from-emerald-100/60 via-teal-50/70 to-sky-100/50 rounded-3xl p-8 border border-emerald-200/60 shadow-xl shadow-emerald-500/5 flex flex-col items-center justify-center text-center relative overflow-hidden">
                <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-md px-3 py-1 rounded-full text-[11px] font-semibold text-emerald-800 border border-emerald-100 shadow-xs flex items-center gap-1">
                  <HeartHandshake className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Safe Space</span>
                </div>
                
                <div className="w-24 h-24 rounded-full bg-white/90 shadow-md border border-emerald-100 flex items-center justify-center text-brand mb-6">
                  <ShieldCheck className="w-12 h-12 text-brand" />
                </div>

                <h3 className="text-xl font-bold text-slate-900 mb-1">
                  100% Verifiable Evidence
                </h3>
                <p className="text-xs text-slate-600 max-w-xs mb-6 leading-relaxed">
                  Every dosage, recovery step, and warning is grounded in verbatim source quotes from your paperwork.
                </p>

                <div className="flex flex-wrap justify-center gap-2">
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/80 text-slate-700 border border-slate-200/60 shadow-xs">
                    Confidential
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/80 text-slate-700 border border-slate-200/60 shadow-xs">
                    Accessible
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/80 text-slate-700 border border-slate-200/60 shadow-xs">
                    Supportive
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* Complete Feature Suite Grid */}
          <section className="flex flex-col gap-10" id="features">
            <div className="text-center max-w-2xl mx-auto">
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                Complete Discharge Care Navigation
              </h2>
              <p className="text-sm sm:text-base text-slate-600 mt-2">
                Integrated features designed to provide comprehensive, accessible, and error-free post-discharge support for patients and caregivers.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Feature 1: AI Fact Extraction */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-emerald-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      AI-Guided Fact Extraction
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Converts unstructured hospital records into clean, categorized patient action items without hallucinating clinical facts.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "care-plan")}
                  className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>Try Demo Report</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 2: Medication Schedules */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-sky-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center">
                    <Pill className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Prescription Schedule Tracker
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Structured medication schedules with exact dosages, intake timings, and food restrictions preserved word-for-word.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "prescriptions")}
                  className="text-xs font-semibold text-sky-700 hover:text-sky-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>View Medication Schedule</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 3: Appointment Tracker */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-purple-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Follow-up Visit Timeline
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Clear chronological timeline of upcoming specialist consultations, wound checks, and diagnostic lab dates.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "appointments")}
                  className="text-xs font-semibold text-purple-700 hover:text-purple-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>View Appointment Timeline</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 4: Conflict Guard */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-rose-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Multi-Document Conflict Guard
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Catches conflicting follow-up dates or differing prescriptions across multiple paperwork pages without guessing.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLoadSample("/sample_conflicting_prescription.pdf", "sample_conflicting_prescription.pdf")}
                  className="text-xs font-semibold text-rose-700 hover:text-rose-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>Test Conflict Demo</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 5: Multilingual Care */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-teal-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center">
                    <Globe className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Source-Preserving Translation
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Instant Google translation to Hindi, Gujarati, Marathi, Tamil, and Telugu while locking drug names, dosages, and dates.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLanguageChange("hi")}
                  className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>Try Hindi / Regional Mode</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 6: Clinical Audit Hub */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-indigo-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
                    <Stethoscope className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Clinical Reviewer Workspace
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Side-by-side evidence comparator allowing authorized healthcare staff to audit and resolve flagged ambiguities.
                    </p>
                  </div>
                </div>
                <a 
                  href="/review"
                  className="text-xs font-semibold text-indigo-700 hover:text-indigo-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>Open Audit Queue</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </a>
              </div>
            </div>

            {/* Bottom Stats Banner */}
            <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-slate-200/80 shadow-xs grid grid-cols-1 sm:grid-cols-3 gap-6 text-center divide-y sm:divide-y-0 sm:divide-x divide-slate-100">
              <div className="flex flex-col items-center justify-center pt-2 sm:pt-0">
                <span className="text-3xl font-extrabold text-slate-900">24/7</span>
                <span className="text-xs font-medium text-slate-500 mt-1">Available Care Plan</span>
              </div>
              <div className="flex flex-col items-center justify-center pt-2 sm:pt-0">
                <span className="text-3xl font-extrabold text-brand">100%</span>
                <span className="text-xs font-medium text-slate-500 mt-1">Verbatim Evidence Grounded</span>
              </div>
              <div className="flex flex-col items-center justify-center pt-2 sm:pt-0">
                <span className="text-3xl font-extrabold text-slate-900">6</span>
                <span className="text-xs font-medium text-slate-500 mt-1">Regional Languages (EN, HI, GU, MR, TA, TE)</span>
              </div>
            </div>
          </section>
        </div>
      ) : (
        /* Active Case Document Navigator */
        <div className="flex flex-col gap-8 fade-in" id="care-plan">
          {/* Active Case Top Control Bar */}
          <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-900 border border-emerald-200">
                  {activeCase.status}
                </span>
                <span className="text-slate-600 text-xs font-mono font-medium">Case #{activeCase.id.substring(0, 8)}</span>
                {isProcessing && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-200 flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin text-amber-700" /> Processing
                  </span>
                )}
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Your Discharge Care Plan</h2>
              <p className="text-xs text-slate-600 mt-0.5 font-medium">
                Extracted from {activeCase.documents.length} document{activeCase.documents.length === 1 ? '' : 's'}. Items marked for review are not yet confirmed.
              </p>
              {language !== "en" && !isTranslating && Object.keys(translations).length === 0 && facts.some(f => f.status === "VERIFIED") && (
                <p role="status" className="text-xs text-amber-800 mt-1 font-medium">{TRANSLATION_UNAVAILABLE[language]}</p>
              )}
            </div>

            {/* Language Switcher and Action Pills */}
            <div className="flex flex-wrap items-center gap-3 no-print">
              {/* Language Selector Pill */}
              <div className="flex items-center bg-slate-100 rounded-full p-1 border border-slate-200 text-xs font-medium">
                <Globe className="w-3.5 h-3.5 text-slate-600 ml-2 mr-1" />
                <button 
                  onClick={() => handleLanguageChange("en")} 
                  className={`px-3 py-1 rounded-full transition-all cursor-pointer ${language === 'en' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  English
                </button>
                <button 
                  onClick={() => handleLanguageChange("hi")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all cursor-pointer ${language === 'hi' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  हिन्दी
                </button>
                <button 
                  onClick={() => handleLanguageChange("gu")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all cursor-pointer ${language === 'gu' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  ગુજરાતી
                </button>
                <button 
                  onClick={() => handleLanguageChange("mr")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all ${language === 'mr' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  मराठी
                </button>
                <button 
                  onClick={() => handleLanguageChange("ta")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all ${language === 'ta' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  தமிழ்
                </button>
                <button 
                  onClick={() => handleLanguageChange("te")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all ${language === 'te' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  తెలుగు
                </button>
                {isTranslating && <Loader2 className="w-3 h-3 animate-spin text-brand ml-1 mr-2" />}
              </div>

              <button
                onClick={() => window.print()}
                className="px-4 py-2 rounded-full bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 text-xs font-bold shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <Printer className="w-3.5 h-3.5 text-slate-700" />
                <span>{ui.printPlan}</span>
              </button>

              {/* Voice Accessibility (Audio Player with Play/Pause/Stop) */}
              <div className="flex items-center gap-1">
                <button
                  onClick={handleToggleReadAloud}
                  className={`px-4 py-2 rounded-full border text-xs font-bold shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer ${
                    ttsState === "playing"
                      ? "bg-amber-50 border-amber-300 text-amber-900"
                      : ttsState === "paused"
                      ? "bg-emerald-50 border-emerald-300 text-emerald-900"
                      : "bg-white hover:bg-slate-50 border-slate-300 text-slate-800"
                  }`}
                  title="Read Aloud (Voice Accessibility with Play/Pause)"
                >
                  {ttsState === "playing" ? (
                    <>
                      <Pause className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
                      <span>{ui.pause}</span>
                    </>
                  ) : ttsState === "paused" ? (
                    <>
                      <Play className="w-3.5 h-3.5 text-emerald-600" />
                      <span>{ui.resume}</span>
                    </>
                  ) : (
                    <>
                      <Volume2 className="w-3.5 h-3.5 text-brand" />
                      <span>{ui.readAloud}</span>
                    </>
                  )}
                </button>
                {ttsState !== "idle" && (
                  <button
                    onClick={handleStopReadAloud}
                    className="px-2.5 py-2 rounded-full bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-bold shadow-xs transition-colors flex items-center gap-1 cursor-pointer"
                    title="Stop Audio"
                  >
                    <Square className="w-3 h-3 fill-current" />
                    <span>{ui.stop}</span>
                  </button>
                )}
              </div>

              <button
                onClick={() => { 
                  setActiveCase(null); 
                  setFacts([]);
                  handleStopReadAloud();
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="px-4 py-2 rounded-full bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-800 text-xs font-bold transition-colors cursor-pointer"
              >
                {ui.newEncounter}
              </button>
            </div>
          </div>

          {/* Attached Files Strip */}
          <div className="flex items-center gap-3 overflow-x-auto pb-1 no-print">
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wider shrink-0">{ui.attachedFiles}</span>
            {activeCase.documents.map(doc => (
              <a
                key={doc.id}
                href={`${API_BASE}/documents/${doc.id}/file`}
                target="_blank"
                rel="noreferrer"
                title="Click to view original source document"
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white hover:bg-slate-50 border border-slate-300 hover:border-emerald-500 text-xs shrink-0 shadow-xs transition-colors group cursor-pointer"
              >
                <FileText className="w-3.5 h-3.5 text-brand" />
                <span className="font-mono text-slate-900 font-semibold">{doc.filename}</span>
                <span className="text-slate-600 text-[11px] capitalize font-medium">• {doc.processing_status.toLowerCase()}</span>
                <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-emerald-600 ml-0.5" />
              </a>
            ))}
          </div>

          {/* Clinical Review & Safety Alerts (with respective Caution Labels & Redirect to /review) */}
          {facts.some(f => f.status === "CONFLICT_DETECTED" || f.status === "NEEDS_REVIEW" || f.status === "HUMAN_REQUIRED") && (
            <div className="p-5 rounded-2xl bg-amber-50/90 border border-amber-300 text-amber-950 flex flex-col gap-4 shadow-xs no-print">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-200 text-amber-800 flex items-center justify-center shrink-0">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-amber-950">{ui.reviewAlertsTitle}</h4>
                    <p className="text-xs text-amber-800 leading-relaxed mt-0.5 max-w-2xl">
                      {ui.reviewAlertsDesc}
                    </p>
                  </div>
                </div>
                <a
                  href={`/review?id=${activeCase.id}`}
                  className="px-4 py-2 rounded-full bg-amber-900 hover:bg-black text-white text-xs font-bold whitespace-nowrap shadow-xs transition-colors flex items-center gap-1.5 shrink-0"
                >
                  <span>{ui.goToReview}</span>
                </a>
              </div>

              {/* Individual Caution Badges List with direct links to /review */}
              <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-amber-200/80">
                {facts
                  .filter(f => f.status === "CONFLICT_DETECTED" || f.status === "NEEDS_REVIEW" || f.status === "HUMAN_REQUIRED")
                  .map(f => {
                    const isConflict = f.status === "CONFLICT_DETECTED";
                    return (
                      <a
                        key={f.id}
                        href={`/review?id=${activeCase.id}&focus=${f.id}`}
                        title="Click to inspect and resolve in Review Queue"
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border transition shadow-2xs ${
                          isConflict 
                            ? "bg-rose-100 hover:bg-rose-200 text-rose-900 border-rose-300" 
                            : "bg-amber-100 hover:bg-amber-200 text-amber-900 border-amber-300"
                        }`}
                      >
                        <span className="font-bold">
                          {isConflict ? `[${ui.cautionConflict}]` : `[${ui.cautionMissingEvidence}]`}
                        </span>
                        <span className="truncate max-w-[200px]">{getFactTitle(f)}</span>
                        <ExternalLink className="w-3 h-3 opacity-70 ml-0.5" />
                      </a>
                    );
                  })}
              </div>
            </div>
          )}

          {/* Care Plan Categorized Sections */}
          {facts.length === 0 && isProcessing ? (
            <div className="py-24 bg-white/60 rounded-3xl border border-slate-200 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-8 h-8 text-brand animate-spin mb-3" />
              <p className="text-base font-bold text-slate-900">Extracting & verifying clinical facts...</p>
              <p className="text-xs text-slate-500 mt-1">Grounding instructions against verbatim source sentences</p>
            </div>
          ) : (
            <>
              {/* Mobile Portrait Dedicated Tab Filter Bar */}
              <div className="md:hidden flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar -mx-1 px-1">
                <button
                  onClick={() => setMobileTab("all")}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all shadow-2xs cursor-pointer ${
                    mobileTab === "all" ? "bg-slate-900 text-white" : "bg-white text-slate-700 border border-slate-200"
                  }`}
                >
                  All Items ({facts.filter(f => f.status !== "REJECTED").length})
                </button>
                {warnings.length > 0 && (
                  <button
                    onClick={() => setMobileTab("warnings")}
                    className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer ${
                      mobileTab === "warnings" ? "bg-rose-600 text-white" : "bg-rose-50 text-rose-800 border border-rose-200"
                    }`}
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Warnings ({warnings.length})</span>
                  </button>
                )}
                {appointments.length > 0 && (
                  <button
                    onClick={() => setMobileTab("followups")}
                    className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer ${
                      mobileTab === "followups" ? "bg-purple-600 text-white" : "bg-purple-50 text-purple-800 border border-purple-200"
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span>Follow-ups ({appointments.length})</span>
                  </button>
                )}
                {medications.length > 0 && (
                  <button
                    onClick={() => setMobileTab("meds")}
                    className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer ${
                      mobileTab === "meds" ? "bg-sky-600 text-white" : "bg-sky-50 text-sky-800 border border-sky-200"
                    }`}
                  >
                    <Pill className="w-3.5 h-3.5" />
                    <span>Prescriptions ({medications.length})</span>
                  </button>
                )}
                {instructions.length > 0 && (
                  <button
                    onClick={() => setMobileTab("instructions")}
                    className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer ${
                      mobileTab === "instructions" ? "bg-emerald-600 text-white" : "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Care Plan ({instructions.length})</span>
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 1. Critical Warnings & Precautions */}
                {warnings.length > 0 && (
                  <section className={`col-span-1 lg:col-span-2 p-6 rounded-3xl bg-rose-50/70 border border-rose-200/80 flex flex-col gap-4 shadow-xs ${mobileTab !== 'all' && mobileTab !== 'warnings' ? 'hidden md:flex' : 'flex'}`} id="warnings">
                  <div className="flex items-center gap-2.5 border-b border-rose-200 pb-3">
                    <div className="w-8 h-8 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-bold text-base text-rose-950">{ui.emergencyWarnings}</h3>
                      <p className="text-xs text-rose-700">{ui.emergencySub}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {warnings.map(f => {
                      const val = f.value || {};
                      const tr = language !== "en" ? translations[f.id] : undefined;
                      const title = String(tr?.title || val.description || val.sign || val.name || getFactTitle(f));
                      const simplified = String(tr?.simplified_meaning || val.simplified_meaning || val.meaning || val.explanation || "").trim();
                      const isConflict = f.status === "CONFLICT_DETECTED";
                      const isMissingEvidence = f.status === "NEEDS_REVIEW" || f.status === "HUMAN_REQUIRED";
                      return (
                        <div 
                          key={f.id} 
                          onClick={() => viewEvidence(f)}
                          className="p-4 rounded-2xl bg-white border border-rose-200 hover:border-rose-400 cursor-pointer transition-all flex flex-col justify-between gap-3 shadow-xs group"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <p className="text-xs font-semibold text-rose-900 leading-relaxed">
                                {title}
                              </p>
                              {Boolean(simplified) && (
                                <p className="text-[11px] text-rose-800 bg-rose-50/90 px-2.5 py-1.5 rounded-xl mt-2 border border-rose-100 flex items-start gap-1.5 leading-snug">
                                  <Sparkles className="w-3 h-3 text-rose-500 shrink-0 mt-0.5" />
                                  <span>{simplified}</span>
                                </p>
                              )}
                            </div>
                            <ChevronRight className="w-4 h-4 text-rose-400 group-hover:translate-x-0.5 transition-transform shrink-0" />
                          </div>
                          <div className="flex items-center justify-between text-[11px] text-rose-600 pt-2 border-t border-rose-100 flex-wrap gap-2">
                            <div className="flex items-center gap-1.5">
                              <StatusBadge status={f.status} lang={language} />
                              {isConflict && (
                                <a
                                  href={`/review?id=${activeCase?.id || ""}&focus=${f.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-900 border border-rose-300 hover:bg-rose-200 transition"
                                  title="Click to resolve this conflict in the Review Queue"
                                >
                                  <span>[{ui.cautionConflict}]</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                              {isMissingEvidence && (
                                <a
                                  href={`/review?id=${activeCase?.id || ""}&focus=${f.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 hover:bg-amber-200 transition"
                                  title="Click to review missing evidence in the Review Queue"
                                >
                                  <span>[{ui.cautionMissingEvidence}]</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                            </div>
                            <span className="font-semibold underline decoration-rose-300">{ui.viewSourceProof}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}

              {/* 2. Upcoming Follow-up Appointments */}
              <section className={`p-6 rounded-3xl bg-white/80 backdrop-blur-md border border-slate-200/80 flex flex-col gap-4 shadow-xs ${mobileTab !== 'all' && mobileTab !== 'followups' ? 'hidden md:flex' : 'flex'}`} id="appointments">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                      <Calendar className="w-4 h-4" />
                    </div>
                    <h3 className="font-bold text-base text-slate-900">{ui.followups}</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">{appointments.length}</span>
                </div>

                {appointments.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4">{ui.followupsEmpty}</p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {appointments.map(f => {
                      const val = f.value || {};
                      const tr = language !== "en" ? translations[f.id] : undefined;
                      const title = String(tr?.title || val.doctor || val.department || val.timing || getFactTitle(f));
                      const subtitle = String(tr?.subtitle || val.date || val.timing || "Clinical Follow-up Visit");
                      const simplified = String(tr?.simplified_meaning || val.simplified_meaning || val.meaning || val.explanation || "").trim();
                      const isConflict = f.status === "CONFLICT_DETECTED";
                      const isMissingEvidence = f.status === "NEEDS_REVIEW" || f.status === "HUMAN_REQUIRED";
                      return (
                        <div 
                          key={f.id} 
                          onClick={() => viewEvidence(f)}
                          className={`p-3.5 sm:p-4 rounded-2xl border transition-all cursor-pointer flex flex-col gap-3 group ${
                            isConflict 
                              ? "bg-rose-50/70 border-rose-300 hover:bg-rose-100/60 shadow-xs" 
                              : "bg-slate-50/80 hover:bg-slate-100/80 border-slate-200/90 shadow-2xs"
                          }`}
                        >
                          {/* Top White Point Tab Header */}
                          <div className="bg-white rounded-xl p-3 sm:p-3.5 border border-slate-200/90 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 w-full">
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                              <div className="w-10 h-10 rounded-xl bg-purple-100 border border-purple-200 flex items-center justify-center text-purple-700 shrink-0 shadow-2xs">
                                <Clock className="w-5 h-5" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <span className="text-sm font-bold text-slate-900 block truncate">
                                  {title}
                                </span>
                                <span className="text-xs font-semibold text-slate-500 block mt-0.5">
                                  {subtitle}
                                </span>
                              </div>
                            </div>

                            <div className="flex items-center gap-2 flex-wrap shrink-0">
                              <StatusBadge status={f.status} lang={language} />
                              {isConflict && (
                                <a
                                  href={`/review?id=${activeCase?.id || ""}&focus=${f.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-100 text-rose-900 border border-rose-300 hover:bg-rose-200 transition"
                                  title="Click to resolve this conflict in the Review Queue"
                                >
                                  <span>[{ui.cautionConflict}]</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                              {isMissingEvidence && (
                                <a
                                  href={`/review?id=${activeCase?.id || ""}&focus=${f.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300 hover:bg-amber-200 transition"
                                  title="Click to review missing evidence in the Review Queue"
                                >
                                  <span>[{ui.cautionMissingEvidence}]</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                              <span className="text-xs font-semibold text-purple-700 hover:underline flex items-center gap-0.5 ml-1">
                                {ui.viewSourceProof}
                                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                              </span>
                            </div>
                          </div>

                          {/* Purple Guidance Paragraph - Cleanly Positioned Below the White Point Tab */}
                          {Boolean(simplified) && (
                            <div className="w-full bg-purple-50/95 border border-purple-200/90 rounded-xl p-3 sm:p-3.5 flex items-start gap-3 shadow-2xs">
                              <div className="w-6 h-6 rounded-lg bg-purple-200/80 text-purple-800 flex items-center justify-center shrink-0 mt-0.5">
                                <Sparkles className="w-3.5 h-3.5 text-purple-700" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-[10px] font-bold tracking-wider uppercase text-purple-900 bg-purple-100/90 px-2 py-0.5 rounded-full border border-purple-200/80">
                                    Plain Language Guidance
                                  </span>
                                </div>
                                <p className="text-xs text-purple-950 leading-relaxed font-medium">
                                  {simplified}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>

              {/* 3. Prescription Medications */}
              <section className={`p-6 rounded-3xl bg-white/80 backdrop-blur-md border border-slate-200/80 flex flex-col gap-4 shadow-xs ${mobileTab !== 'all' && mobileTab !== 'meds' ? 'hidden md:flex' : 'flex'}`} id="prescriptions">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center">
                      <Pill className="w-4 h-4" />
                    </div>
                    <h3 className="font-bold text-base text-slate-900">{ui.prescriptions}</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">{medications.length}</span>
                </div>

                {medications.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4">{ui.prescriptionsEmpty}</p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {medications.map(f => {
                      const val = f.value || {};
                      const tr = language !== "en" ? translations[f.id] : undefined;
                      const name = String(tr?.title || val.name || getFactTitle(f));
                      const subtitle = tr?.subtitle || (val.frequency ? `${ui.instructionsLabel} ${String(val.frequency)}` : "");
                      const simplified = String(tr?.simplified_meaning || val.simplified_meaning || val.meaning || val.explanation || "").trim();
                      const isConflict = f.status === "CONFLICT_DETECTED";
                      const isMissingEvidence = f.status === "NEEDS_REVIEW" || f.status === "HUMAN_REQUIRED";
                      return (
                        <div 
                          key={f.id} 
                          onClick={() => viewEvidence(f)}
                          className={`p-4 rounded-2xl border transition-all cursor-pointer flex flex-col gap-2 group ${
                            isConflict 
                              ? "bg-rose-50 border-rose-300 hover:bg-rose-100/50" 
                              : "bg-white hover:bg-slate-50 border-slate-200 shadow-xs"
                          }`}
                        >
                          <div className="flex items-center justify-between flex-wrap gap-2">
                            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                              <Pill className="w-3.5 h-3.5 text-brand" />
                              {name}
                            </span>
                            <div className="flex items-center gap-1.5 flex-wrap">
                              {Boolean(val.strength) && (
                                <span className="text-[11px] font-mono font-semibold text-emerald-800 px-2.5 py-0.5 rounded-full bg-emerald-100">
                                  {String(val.strength)}
                                </span>
                              )}
                              <StatusBadge status={f.status} lang={language} />
                              {isConflict && (
                                <a
                                  href={`/review?id=${activeCase?.id || ""}&focus=${f.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-900 border border-rose-300 hover:bg-rose-200 transition"
                                  title="Click to resolve this conflict in the Review Queue"
                                >
                                  <span>[{ui.cautionConflict}]</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                              {isMissingEvidence && (
                                <a
                                  href={`/review?id=${activeCase?.id || ""}&focus=${f.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 hover:bg-amber-200 transition"
                                  title="Click to review missing evidence in the Review Queue"
                                >
                                  <span>[{ui.cautionMissingEvidence}]</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                            </div>
                          </div>

                          {Boolean(simplified) && (
                            <div className="text-[11px] text-slate-700 bg-emerald-50/70 p-2.5 rounded-xl border border-emerald-100 flex items-start gap-1.5 leading-snug">
                              <Sparkles className="w-3 h-3 text-emerald-600 shrink-0 mt-0.5" />
                              <span>{simplified}</span>
                            </div>
                          )}

                          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                            <span>{subtitle}</span>
                            <span className="font-semibold text-brand underline decoration-emerald-200 group-hover:decoration-brand">{ui.viewSourceProof}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>

              {/* 4. Home Care & Recovery Instructions */}
              <section className={`col-span-1 lg:col-span-2 p-6 rounded-3xl bg-white/80 backdrop-blur-md border border-slate-200/80 flex flex-col gap-4 shadow-xs ${mobileTab !== 'all' && mobileTab !== 'instructions' ? 'hidden md:flex' : 'flex'}`} id="instructions">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center">
                      <Activity className="w-4 h-4" />
                    </div>
                    <h3 className="font-bold text-base text-slate-900">{ui.homeCare}</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">{instructions.length}</span>
                </div>

                {instructions.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4">{ui.homeCareEmpty}</p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {instructions.map(f => {
                      const val = f.value || {};
                      const tr = language !== "en" ? translations[f.id] : undefined;
                      const title = String(tr?.title || val.instruction || val.text || val.guideline || getFactTitle(f));
                      const simplified = String(tr?.simplified_meaning || val.simplified_meaning || val.meaning || val.explanation || "").trim();
                      const isConflict = f.status === "CONFLICT_DETECTED";
                      const isMissingEvidence = f.status === "NEEDS_REVIEW" || f.status === "HUMAN_REQUIRED";
                      return (
                        <div 
                          key={f.id} 
                          onClick={() => viewEvidence(f)}
                          className="p-4 rounded-2xl bg-white hover:bg-slate-50 border border-slate-200 cursor-pointer transition-all flex flex-col justify-between gap-3 shadow-xs group"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <p className="text-xs font-medium text-slate-800 leading-relaxed">
                                {title}
                              </p>
                              {Boolean(simplified) && (
                                <p className="text-[11px] text-teal-800 bg-teal-50/80 p-2 rounded-xl mt-2 border border-teal-100 flex items-start gap-1.5 leading-snug">
                                  <Sparkles className="w-3 h-3 text-teal-600 shrink-0 mt-0.5" />
                                  <span>{simplified}</span>
                                </p>
                              )}
                            </div>
                            <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform shrink-0" />
                          </div>
                          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100 flex-wrap gap-2">
                            <div className="flex items-center gap-1.5">
                              <StatusBadge status={f.status} lang={language} />
                              {isConflict && (
                                <a
                                  href={`/review?id=${activeCase?.id || ""}&focus=${f.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-900 border border-rose-300 hover:bg-rose-200 transition"
                                  title="Click to resolve this conflict in the Review Queue"
                                >
                                  <span>[{ui.cautionConflict}]</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                              {isMissingEvidence && (
                                <a
                                  href={`/review?id=${activeCase?.id || ""}&focus=${f.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 hover:bg-amber-200 transition"
                                  title="Click to review missing evidence in the Review Queue"
                                >
                                  <span>[{ui.cautionMissingEvidence}]</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              )}
                            </div>
                            <span className="font-semibold text-brand underline decoration-emerald-200">{ui.viewSourceProof}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            </div>
          </>
        )}
        </div>
      )}

      {/* Floating Centered Verbatim Evidence Modal Pop-Up */}
      {selectedFact && (
        <div 
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-md z-50 flex items-center justify-center p-4 sm:p-6 no-print animate-in fade-in duration-150"
          onClick={() => setSelectedFact(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="evidence-modal-title"
        >
          <div 
            className="w-full max-w-xl max-h-[85vh] rounded-3xl bg-white border border-slate-200 shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/60">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h2 id="evidence-modal-title" className="text-base font-bold text-slate-900">Verbatim Source Proof</h2>
                  <p className="text-[11px] text-slate-500">Grounding verification from original hospital paperwork</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedFact(null)} 
                className="p-1.5 rounded-full bg-white hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors border border-slate-200 cursor-pointer"
                aria-label="Close evidence popup"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Scrollable Body */}
            <div className="p-6 overflow-y-auto flex flex-col gap-5 custom-scrollbar">
              {/* Fact Summary */}
              <div>
                <span className="text-[11px] text-slate-700 uppercase tracking-wider font-bold">Extracted Clinical Fact</span>
                <div className="mt-1.5 p-3.5 rounded-2xl bg-slate-50 border border-slate-300 text-sm font-bold text-slate-900 shadow-xs">
                  {getFactTitle(selectedFact)}
                </div>

                {(() => {
                  const mVal = (language === "en" || !translations[selectedFact.id] ? selectedFact.value : translations[selectedFact.id]) || {};
                  const mSimp = mVal.simplified_meaning || mVal.meaning || mVal.explanation;
                  if (!mSimp) return null;
                  return (
                    <div className="mt-3 p-3.5 rounded-2xl bg-emerald-50/90 border border-emerald-200 text-xs text-slate-800 flex items-start gap-2.5 shadow-xs">
                      <Sparkles className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-emerald-950 block mb-0.5">AI Plain-Language Patient Guide:</span>
                        <span className="text-slate-700 leading-relaxed">{String(mSimp)}</span>
                      </div>
                    </div>
                  );
                })()}

                {/* Status Badge */}
                <div className="mt-2.5 flex items-center gap-2">
                  <StatusBadge status={selectedFact.status} lang={language} />
                </div>

                {selectedFact.status_reasons && selectedFact.status_reasons.length > 0 && (
                  <div className="mt-3 p-3.5 bg-amber-50 border border-amber-300 rounded-2xl text-xs text-amber-950">
                    <span className="font-bold text-amber-900 block mb-1">Status Rationale:</span>
                    <ul className="list-disc list-inside space-y-1 text-amber-900 font-medium">
                      {selectedFact.status_reasons.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}
              </div>

              {/* Source Document Citations */}
              <div className="flex flex-col gap-3">
                <span className="text-[11px] text-slate-700 uppercase tracking-wider font-bold">Exact Excerpt in Source Paperwork</span>
                
                {isFetchingEvidence ? (
                  <div className="p-8 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-brand" /></div>
                ) : evidence.length > 0 ? (
                  evidence.map(ev => {
                    const doc = activeCase?.documents.find(d => d.id === ev.document_id);
                    return (
                      <div key={ev.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-300 flex flex-col gap-3 shadow-xs">
                        <div className="flex items-center justify-between text-xs text-slate-700 border-b border-slate-200 pb-2">
                          <span className="font-mono font-bold text-slate-900 truncate max-w-[240px]">{doc?.filename || "Medical Document"}</span>
                          <span className="px-2.5 py-0.5 rounded-full bg-white border border-slate-300 text-slate-800 font-mono text-[11px] font-semibold">Page {ev.page_number}</span>
                        </div>

                        {ev.snippet ? (
                          <div className="p-3.5 bg-amber-50 border-l-4 border-amber-500 rounded-r-xl text-xs leading-relaxed italic text-slate-900 font-medium select-text">
                            &quot;{ev.snippet}&quot;
                          </div>
                        ) : (
                          <p className="text-xs text-amber-900 italic font-medium">No direct excerpt captured.</p>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-slate-600 text-center p-4 font-medium">No evidence citations linked.</p>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/60 flex justify-end">
              <button
                onClick={() => setSelectedFact(null)}
                className="px-5 py-2 rounded-full bg-brand hover:bg-brand-light text-white text-xs font-semibold transition-colors shadow-xs cursor-pointer"
              >
                Close Proof
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pre-Upload Health Data Privacy & Legal Consent Gateway Modal */}
      {showUploadConsentModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="upload-consent-title"
          aria-describedby="upload-consent-desc"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn"
          onClick={() => setShowUploadConsentModal(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-xl bg-white border border-slate-200 rounded-3xl shadow-2xl p-6 sm:p-8 flex flex-col gap-6 text-slate-900 max-h-[90vh] overflow-y-auto custom-scrollbar"
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                  <Lock className="w-5 h-5 text-emerald-700" aria-hidden="true" />
                </div>
                <div>
                  <h2 id="upload-consent-title" className="text-lg font-bold text-slate-900">
                    Patient Paperwork Privacy & Consent
                  </h2>
                  <p id="upload-consent-desc" className="text-xs text-slate-500">
                    Required active consent under GDPR, CCPA, and HIPAA guidelines
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowUploadConsentModal(false)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
                aria-label="Close upload consent dialog"
              >
                <X className="w-5 h-5" aria-hidden="true" />
              </button>
            </div>

            {/* Safeguards Summary */}
            <div className="flex flex-col gap-2.5 text-xs text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-200">
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <strong className="text-slate-900">Isolated & Private Processing:</strong> Your discharge paperwork is stored securely under randomized UUID keys and never exposed to public directories.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <strong className="text-slate-900">Zero Commercial Model Training:</strong> Your clinical paperwork is never ingested or shared to train public commercial AI models.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <strong className="text-slate-900">Data Minimization:</strong> Only clinical instructions, follow-ups, and medications from the document are extracted.
                </div>
              </div>
            </div>

            {/* Unchecked Active Opt-in Checkboxes */}
            <div className="flex flex-col gap-3.5">
              <div className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors">
                <input
                  id="consent-age-check"
                  type="checkbox"
                  checked={consentAge}
                  onChange={(e) => setConsentAge(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded border-slate-300 text-emerald-600 focus-visible:outline-2 focus-visible:outline-emerald-600 shrink-0 cursor-pointer"
                />
                <label htmlFor="consent-age-check" className="text-xs text-slate-800 leading-relaxed cursor-pointer">
                  <strong>Age & Authority Attestation:</strong> I confirm that I am at least 18 years old, or the legally authorized parent, guardian, or primary caregiver of the patient.
                </label>
              </div>

              <div className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors">
                <input
                  id="consent-privacy-check"
                  type="checkbox"
                  checked={consentPrivacy}
                  onChange={(e) => setConsentPrivacy(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded border-slate-300 text-emerald-600 focus-visible:outline-2 focus-visible:outline-emerald-600 shrink-0 cursor-pointer"
                />
                <label htmlFor="consent-privacy-check" className="text-xs text-slate-800 leading-relaxed cursor-pointer">
                  <strong>Health Data Processing Consent:</strong> I grant explicit consent to extract and translate discharge directions from this paperwork in accordance with the{" "}
                  <a href="/privacy" target="_blank" rel="noopener noreferrer" className="text-emerald-700 underline font-semibold">
                    Privacy Policy
                  </a>{" "}
                  and{" "}
                  <a href="/terms" target="_blank" rel="noopener noreferrer" className="text-emerald-700 underline font-semibold">
                    Terms of Service
                  </a>.
                </label>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowUploadConsentModal(false)}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-slate-700 font-semibold text-xs transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!consentAge || !consentPrivacy}
                onClick={handleConfirmUploadConsent}
                className={`w-full sm:w-auto px-6 py-2.5 rounded-xl font-bold text-xs shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600 ${
                  consentAge && consentPrivacy
                    ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20"
                    : "bg-slate-200 text-slate-400 cursor-not-allowed shadow-none"
                }`}
                id="btn-confirm-upload-consent"
              >
                <Check className="w-4 h-4" aria-hidden="true" />
                <span>Agree & Select Document</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Authentication Modal (OWASP Compliant User Isolation) */}
      {showAuthModal && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200"
          role="dialog"
          aria-modal="true"
          aria-labelledby="auth-modal-title"
        >
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-100 max-w-md w-full p-6 sm:p-8 relative">
            <button
              onClick={() => setShowAuthModal(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-600 p-1.5 rounded-full hover:bg-slate-100 transition-colors"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-2xl bg-teal-50 flex items-center justify-center text-teal-600 border border-teal-100">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h3 id="auth-modal-title" className="text-xl font-black text-slate-900 tracking-tight">
                  {authMode === "login" ? "Sign In to CARELYNX" : "Create Isolated Account"}
                </h3>
                <p className="text-xs text-slate-500">
                  {authMode === "login" 
                    ? "Access your encrypted private medical history." 
                    : "Zero data leakage — your medical records remain completely isolated."}
                </p>
              </div>
            </div>

            {authError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-700 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{authError}</span>
              </div>
            )}

            <form onSubmit={handleAuthSubmit} className="space-y-4">
              {authMode === "register" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={authName}
                      onChange={(e) => setAuthName(e.target.value)}
                      placeholder="Jane Doe"
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    placeholder="patient@example.com"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
                <div className="relative">
                  <Key className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                  />
                </div>
                {authMode === "register" && (
                  <p className="text-[10px] text-slate-400 mt-1">Must be at least 8 characters with a letter and a number.</p>
                )}
              </div>

              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white shadow-lg shadow-teal-600/20 transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {authLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                <span>{authMode === "login" ? "Sign In" : "Create Account"}</span>
              </button>
            </form>

            <div className="mt-5 text-center text-xs text-slate-500">
              {authMode === "login" ? (
                <span>
                  Don&apos;t have an account?{" "}
                  <button
                    type="button"
                    onClick={() => { setAuthMode("register"); setAuthError(null); }}
                    className="font-bold text-teal-600 hover:underline cursor-pointer"
                  >
                    Register here
                  </button>
                </span>
              ) : (
                <span>
                  Already registered?{" "}
                  <button
                    type="button"
                    onClick={() => { setAuthMode("login"); setAuthError(null); }}
                    className="font-bold text-teal-600 hover:underline cursor-pointer"
                  >
                    Sign in
                  </button>
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Medical History Drawer (User-Specific Case Isolation) */}
      {showHistoryDrawer && (
        <div 
          className="fixed inset-0 z-50 flex justify-end bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200"
          role="dialog"
          aria-modal="true"
        >
          <div className="bg-white w-full max-w-md h-full shadow-2xl flex flex-col border-l border-slate-100 animate-in slide-in-from-right duration-200">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-teal-50 flex items-center justify-center text-teal-600 border border-teal-100">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-black text-slate-900 text-base">Your Medical History</h3>
                  <p className="text-xs text-slate-500">{currentUser?.email} (Private)</p>
                </div>
              </div>
              <button
                onClick={() => setShowHistoryDrawer(false)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-full hover:bg-slate-100 transition-colors"
                aria-label="Close history"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-3">
              {loadingCases ? (
                <div className="flex flex-col items-center justify-center h-48 text-slate-400 gap-3">
                  <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
                  <span className="text-xs">Loading your secure cases...</span>
                </div>
              ) : userCases.length === 0 ? (
                <div className="text-center py-12 px-4">
                  <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                  <p className="text-sm font-semibold text-slate-700">No records found</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
                    Any discharge summaries or clinical notes you upload while logged in will be safely preserved here.
                  </p>
                </div>
              ) : (
                userCases.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => handleSelectHistoryCase(c)}
                    className="p-4 rounded-2xl border border-slate-100 hover:border-teal-200 bg-slate-50/50 hover:bg-teal-50/20 transition cursor-pointer group flex items-start justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-black text-slate-900 group-hover:text-teal-700 transition">
                          Case #{c.id.substring(0, 8)}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                          c.status === "completed" 
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200" 
                            : "bg-amber-50 text-amber-700 border border-amber-200"
                        }`}>
                          {c.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500">
                        {c.created_at ? new Date(c.created_at).toLocaleString() : "Recent record"}
                      </p>
                      {c.documents && c.documents.length > 0 && (
                        <p className="text-[11px] text-slate-400 mt-1 truncate max-w-[240px]">
                          📄 {c.documents[0].filename}
                        </p>
                      )}
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-0.5 transition shrink-0 mt-1" />
                  </div>
                ))
              )}
            </div>

            <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
              <span className="text-xs text-slate-500">Tenant-isolated storage</span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 text-xs font-bold text-rose-600 hover:text-rose-700 hover:underline cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Patient Profile Modal (Stored in single table 'user_data') */}
      {showProfileModal && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200"
          role="dialog"
          aria-modal="true"
        >
          <div className="bg-white rounded-3xl max-w-xl w-full p-6 sm:p-8 shadow-2xl border border-slate-100 flex flex-col max-h-[90vh] overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100 font-bold">
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-lg leading-tight">Patient Profile Details</h3>
                  <p className="text-xs text-slate-500">Securely encrypted & stored with strict patient confidentiality</p>
                </div>
              </div>
              <button
                onClick={() => setShowProfileModal(false)}
                className="text-slate-400 hover:text-slate-600 p-2 rounded-full hover:bg-slate-100 transition-colors cursor-pointer"
                aria-label="Close profile modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scrollable Form Content */}
            <div className="flex-1 overflow-y-auto py-5 space-y-5 custom-scrollbar pr-1">
              {profileLoading ? (
                <div className="flex flex-col items-center justify-center py-12 text-slate-400 gap-3">
                  <Loader2 className="w-7 h-7 animate-spin text-blue-600" />
                  <span className="text-xs">Loading profile details...</span>
                </div>
              ) : (
                <form onSubmit={handleSaveProfile} id="profile-edit-form" className="space-y-4">
                  {profileSuccessMsg && (
                    <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span className="font-semibold">{profileSuccessMsg}</span>
                    </div>
                  )}

                  {profileErrorMsg && (
                    <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                      <span className="font-semibold">{profileErrorMsg}</span>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">
                        Full Legal Name
                      </label>
                      <input
                        type="text"
                        value={profileData.displayName}
                        onChange={e => setProfileData(prev => ({ ...prev, displayName: e.target.value }))}
                        placeholder="e.g. John Doe"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">
                        Account Email
                      </label>
                      <input
                        type="email"
                        value={profileData.email}
                        disabled
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs sm:text-sm text-slate-500 cursor-not-allowed"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">
                        Contact Phone Number
                      </label>
                      <input
                        type="tel"
                        value={profileData.phone || ""}
                        onChange={e => setProfileData(prev => ({ ...prev, phone: e.target.value }))}
                        placeholder="e.g. +91 98765 43210"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">
                        Date of Birth
                      </label>
                      <input
                        type="date"
                        value={profileData.dob || ""}
                        onChange={e => setProfileData(prev => ({ ...prev, dob: e.target.value }))}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">
                        Emergency Contact Person
                      </label>
                      <input
                        type="text"
                        value={profileData.emergencyContactName || ""}
                        onChange={e => setProfileData(prev => ({ ...prev, emergencyContactName: e.target.value }))}
                        placeholder="e.g. Jane Doe (Spouse)"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">
                        Emergency Phone
                      </label>
                      <input
                        type="tel"
                        value={profileData.emergencyContactPhone || ""}
                        onChange={e => setProfileData(prev => ({ ...prev, emergencyContactPhone: e.target.value }))}
                        placeholder="e.g. +91 98765 43211"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">
                        Blood Group
                      </label>
                      <select
                        value={profileData.bloodGroup || "Unknown"}
                        onChange={e => setProfileData(prev => ({ ...prev, bloodGroup: e.target.value }))}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white"
                      >
                        <option value="Unknown">Unknown / Not Tested</option>
                        <option value="A+">A Positive (A+)</option>
                        <option value="A-">A Negative (A-)</option>
                        <option value="B+">B Positive (B+)</option>
                        <option value="B-">B Negative (B-)</option>
                        <option value="AB+">AB Positive (AB+)</option>
                        <option value="AB-">AB Negative (AB-)</option>
                        <option value="O+">O Positive (O+)</option>
                        <option value="O-">O Negative (O-)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">
                        Preferred Language
                      </label>
                      <select
                        value={profileData.preferredLanguage || "en"}
                        onChange={e => setProfileData(prev => ({ ...prev, preferredLanguage: e.target.value }))}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white"
                      >
                        <option value="en">English</option>
                        <option value="hi">हिंदी (Hindi)</option>
                        <option value="gu">ગુજરાતી (Gujarati)</option>
                        <option value="mr">मराठी (Marathi)</option>
                        <option value="ta">தமிழ் (Tamil)</option>
                        <option value="te">తెలుగు (Telugu)</option>
                      </select>
                    </div>
                  </div>

                  {/* Activity log preview from single table */}
                  {profileActivities.length > 0 && (
                    <div className="pt-4 border-t border-slate-100">
                      <span className="text-xs font-bold text-slate-700 block mb-2">
                        Recent Account Activities
                      </span>
                      <div className="max-h-32 overflow-y-auto divide-y divide-slate-100 bg-slate-50 rounded-xl p-2.5 border border-slate-200 text-[11px]">
                        {profileActivities.slice(0, 5).map((act: UserActivityItem, idx: number) => (
                          <div key={act.id || idx} className="py-1.5 flex items-center justify-between">
                            <span className="font-semibold text-slate-800">{act.description || act.action}</span>
                            <span className="text-slate-400 font-mono text-[10px]">
                              {act.timestamp ? new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </form>
              )}
            </div>

            {/* Footer Actions */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setShowProfileModal(false)}
                className="px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs sm:text-sm font-semibold transition cursor-pointer"
              >
                Close
              </button>

              <button
                type="submit"
                form="profile-edit-form"
                disabled={profileSaving || profileLoading}
                className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs sm:text-sm font-semibold flex items-center gap-2 transition disabled:opacity-50 cursor-pointer shadow-sm"
              >
                {profileSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Saving changes...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Save Profile Details</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Portrait Dedicated Bottom Action Floating Bar */}
      {activeCase && (
        <div className="md:hidden fixed bottom-3 inset-x-3 z-30 bg-white/95 backdrop-blur-md rounded-2xl p-2.5 border border-slate-200/90 shadow-xl flex items-center justify-between gap-2 no-print">
          <button
            onClick={handleToggleReadAloud}
            className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all shadow-2xs cursor-pointer ${
              ttsState === "playing"
                ? "bg-amber-500 text-white"
                : ttsState === "paused"
                ? "bg-emerald-600 text-white"
                : "bg-slate-100 text-slate-800 border border-slate-200"
            }`}
          >
            {ttsState === "playing" ? (
              <>
                <Pause className="w-4 h-4 animate-pulse" />
                <span>{ui.pause}</span>
              </>
            ) : ttsState === "paused" ? (
              <>
                <Play className="w-4 h-4" />
                <span>{ui.resume}</span>
              </>
            ) : (
              <>
                <Volume2 className="w-4 h-4 text-emerald-600" />
                <span>{ui.readAloud}</span>
              </>
            )}
          </button>

          {ttsState !== "idle" && (
            <button
              onClick={handleStopReadAloud}
              className="p-2 rounded-xl bg-rose-50 text-rose-600 border border-rose-200 shadow-2xs cursor-pointer"
              title="Stop Read Aloud"
            >
              <Square className="w-4 h-4 fill-current" />
            </button>
          )}

          <button
            onClick={() => {
              const langs: ("en" | "hi" | "gu" | "mr" | "ta" | "te")[] = ["en", "hi", "gu", "mr", "ta", "te"];
              const nextIndex = (langs.indexOf(language) + 1) % langs.length;
              handleLanguageChange(langs[nextIndex]);
            }}
            className="py-2 px-3 rounded-xl bg-slate-100 border border-slate-200 text-xs font-bold text-slate-700 flex items-center gap-1 shadow-2xs cursor-pointer"
            title="Cycle Language"
          >
            <Languages className="w-3.5 h-3.5 text-blue-600" />
            <span className="uppercase">{language}</span>
          </button>

          <button
            onClick={initiateUploadClick}
            className="py-2 px-3 rounded-xl bg-brand hover:bg-brand-light text-white text-xs font-bold flex items-center gap-1 shadow-xs cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-white" />
            <span>Upload</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-brand" />
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}

// Status wording must never read as more certain than the backend status (SAFETY.md §5).
const STATUS_LABELS: Record<string, Record<Lang, string>> = {
  VERIFIED: { en: "✓ Verified", hi: "✓ सत्यापित", gu: "✓ ચકાસાયેલ", mr: "✓ पडताळलेले", ta: "✓ சரிபார்க்கப்பட்டது", te: "✓ ధృవీకరించబడింది" },
  NEEDS_REVIEW: { en: "⚠ Needs review", hi: "⚠ समीक्षा आवश्यक", gu: "⚠ સમીક્ષા જરૂરી", mr: "⚠ पुनरावलोकन आवश्यक", ta: "⚠ மதிப்பாய்வு தேவை", te: "⚠ సమీక్ష అవసరం" },
  HUMAN_REQUIRED: { en: "🔴 Human review required", hi: "🔴 मानव समीक्षा आवश्यक", gu: "🔴 માનવ સમીક્ષા જરૂરી", mr: "🔴 मानवी पुनरावलोकन आवश्यक", ta: "🔴 மனித மதிப்பாய்வு தேவை", te: "🔴 మానవ సమీక్ష అవసరం" },
  CONFLICT_DETECTED: { en: "🔴 Conflict — human review required", hi: "🔴 विरोधाभास — मानव समीक्षा आवश्यक", gu: "🔴 વિરોધાભાસ — માનવ સમીક્ષા જરૂરી", mr: "🔴 विसंगती — मानवी पुनरावलोकन आवश्यक", ta: "🔴 முரண்பாடு — மனித மதிப்பாய்வு தேவை", te: "🔴 వైరుధ్యం — మానవ సమీక్ష అవసరం" },
};

const STATUS_STYLES: Record<string, string> = {
  VERIFIED: "bg-emerald-100 text-emerald-900 border-emerald-300",
  NEEDS_REVIEW: "bg-amber-100 text-amber-900 border-amber-300",
  HUMAN_REQUIRED: "bg-rose-100 text-rose-900 border-rose-300",
  CONFLICT_DETECTED: "bg-rose-100 text-rose-900 border-rose-300",
};

function StatusBadge({ status, lang }: { status: string; lang: Lang }) {
  const label = STATUS_LABELS[status]?.[lang] ?? STATUS_LABELS.NEEDS_REVIEW[lang];
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${STATUS_STYLES[status] ?? STATUS_STYLES.NEEDS_REVIEW}`}>
      {label}
    </span>
  );
}

const SPEECH_LANG: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", gu: "gu-IN", mr: "mr-IN", ta: "ta-IN", te: "te-IN" };

const READ_ALOUD_INTRO: Record<Lang, string> = {
  en: "Reading your care plan.",
  hi: "आपकी देखभाल योजना पढ़ी जा रही है।",
  gu: "તમારી સંભાળ યોજના વાંચવામાં આવી રહી છે.",
  mr: "तुमची काळजी योजना वाचली जात आहे.",
  ta: "உங்கள் பராமரிப்பு திட்டம் வாசிக்கப்படுகிறது.",
  te: "మీ సంరక్షణ ప్రణాళిక చదవబడుతోంది.",
};

const TRANSLATION_UNAVAILABLE: Record<Lang, string> = {
  en: "",
  hi: "अनुवाद सेवा अभी उपलब्ध नहीं है — मूल अंग्रेज़ी पाठ दिखाया जा रहा है।",
  gu: "અનુવાદ સેવા હાલમાં ઉપલબ્ધ નથી — મૂળ અંગ્રેજી લખાણ બતાવવામાં આવી રહ્યું છે.",
  mr: "भाषांतर सेवा सध्या उपलब्ध नाही — मूळ इंग्रजी मजकूर दाखवला जात आहे.",
  ta: "மொழிபெயர்ப்பு சேவை இப்போது கிடைக்கவில்லை — அசல் ஆங்கில உரை காட்டப்படுகிறது.",
  te: "అనువాద సేవ ప్రస్తుతం అందుబాటులో లేదు — అసలు ఆంగ్ల వచనం చూపబడుతోంది.",
};
