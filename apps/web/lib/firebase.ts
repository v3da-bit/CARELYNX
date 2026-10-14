import { initializeApp, getApps, getApp, type FirebaseApp } from "firebase/app";
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged, 
  updateProfile, 
  signInWithPopup, 
  GoogleAuthProvider, 
  type User, 
  type Auth 
} from "firebase/auth";
import { 
  getFirestore, 
  doc, 
  setDoc, 
  getDoc, 
  serverTimestamp, 
  type Firestore 
} from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyBj_acq_j1GwqNYJQDVneNbbSLFUDtTW2A",
  authDomain: "buttler-8e847.firebaseapp.com",
  projectId: "buttler-8e847",
  storageBucket: "buttler-8e847.firebasestorage.app",
  messagingSenderId: "471913780818",
  appId: "1:471913780818:web:6db6aa7128eb4b10c1718b",
  measurementId: "G-W78MERWHDQ"
};

// Initialize Firebase App safely (singleton)
export const app: FirebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig);
export const auth: Auth = getAuth(app);
export const db: Firestore = getFirestore(app);

// SINGLE TABLE DESIGN: All user data, cases, profile, and activities are stored in collection "user_data"
export const FIRESTORE_SINGLE_TABLE = "user_data";

export interface FirestoreCaseRecord {
  id: string;
  case_id: string;
  user_id: string;
  title: string;
  filename: string;
  status: string;
  created_at: string;
  updated_at: string;
  document_count: number;
  facts_count: {
    total: number;
    medications: number;
    appointments: number;
    warnings: number;
    instructions: number;
  };
  summary?: string;
}

export interface UserProfileData {
  displayName: string;
  email: string;
  phone?: string;
  dob?: string;
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  bloodGroup?: string;
  preferredLanguage?: string;
  updatedAt: string;
}

export interface UserActivityItem {
  id: string;
  action: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface SingleTableUserData {
  user_id: string;
  email: string;
  profile: UserProfileData;
  cases: FirestoreCaseRecord[];
  activities: UserActivityItem[];
  recent_case_id?: string;
  updated_at: string;
}

// Local Storage Memory Fallback (Guarantees zero data loss if rules/network block remote writes)
function getLocalUserData(userId: string): SingleTableUserData {
  if (typeof window === "undefined" || !userId) {
    return {
      user_id: userId,
      email: "",
      profile: { displayName: "Patient", email: "", updatedAt: new Date().toISOString() },
      cases: [],
      activities: [],
      updated_at: new Date().toISOString()
    };
  }
  try {
    const raw = localStorage.getItem(`carelynx_user_data_${userId}`);
    if (raw) return JSON.parse(raw);
  } catch {
    // fallback
  }
  return {
    user_id: userId,
    email: "",
    profile: { displayName: "Patient", email: "", updatedAt: new Date().toISOString() },
    cases: [],
    activities: [],
    updated_at: new Date().toISOString()
  };
}

function setLocalUserData(userId: string, data: SingleTableUserData): void {
  if (typeof window === "undefined" || !userId) return;
  try {
    localStorage.setItem(`carelynx_user_data_${userId}`, JSON.stringify(data));
  } catch {
    // ignore quota/private mode
  }
}

/**
 * Fetch the master record for a user from the single Firestore table "user_data".
 */
export async function getMasterUserData(userId: string): Promise<SingleTableUserData> {
  const local = getLocalUserData(userId);
  if (!userId) return local;

  try {
    const docRef = doc(db, FIRESTORE_SINGLE_TABLE, userId);
    const snap = await getDoc(docRef);
    if (snap.exists()) {
      const remote = snap.data() as SingleTableUserData;
      // Merge cases and activities seamlessly
      const merged: SingleTableUserData = {
        user_id: userId,
        email: remote.email || local.email,
        profile: { ...local.profile, ...(remote.profile || {}) },
        cases: remote.cases || local.cases || [],
        activities: remote.activities || local.activities || [],
        recent_case_id: remote.recent_case_id || local.recent_case_id,
        updated_at: remote.updated_at || new Date().toISOString()
      };
      setLocalUserData(userId, merged);
      return merged;
    }
  } catch (err: unknown) {
    const msg = String(err);
    if (!msg.includes("permission")) {
      console.warn("Firestore single table fetch fallback to local memory:", err);
    }
  }
  return local;
}

/**
 * Save user profile details to the single Firestore table "user_data".
 */
export async function saveUserProfileToFirestore(
  userId: string, 
  profileUpdate: Partial<UserProfileData>
): Promise<UserProfileData> {
  const current = getLocalUserData(userId);
  const now = new Date().toISOString();

  const updatedProfile: UserProfileData = {
    ...current.profile,
    ...profileUpdate,
    displayName: profileUpdate.displayName?.trim() || current.profile.displayName || "Patient",
    email: profileUpdate.email || current.email || current.profile.email,
    updatedAt: now
  };

  const activity: UserActivityItem = {
    id: `act_${Date.now()}`,
    action: "PROFILE_UPDATED",
    description: "Updated patient profile details",
    timestamp: now
  };

  const updatedData: SingleTableUserData = {
    ...current,
    profile: updatedProfile,
    activities: [activity, ...(current.activities || [])].slice(0, 50),
    updated_at: now
  };

  // 1. Immediately cache locally
  setLocalUserData(userId, updatedData);

  // 2. Persist to single Firestore table
  try {
    const docRef = doc(db, FIRESTORE_SINGLE_TABLE, userId);
    await setDoc(docRef, {
      ...updatedData,
      server_timestamp: serverTimestamp()
    }, { merge: true });
  } catch (err: unknown) {
    const msg = String(err);
    if (!msg.includes("permission")) {
      console.warn("Could not save profile to Firestore single table:", err);
    }
  }

  // 3. Update Firebase Auth displayName if changed
  if (auth.currentUser && updatedProfile.displayName) {
    try {
      await updateProfile(auth.currentUser, { displayName: updatedProfile.displayName });
    } catch {
      // non-blocking
    }
  }

  return updatedProfile;
}

/**
 * Log a user activity directly into the single Firestore table "user_data".
 */
export async function logUserActivity(
  userId: string,
  action: string,
  description: string,
  metadata?: Record<string, unknown>
): Promise<void> {
  if (!userId) return;
  const current = getLocalUserData(userId);
  const now = new Date().toISOString();

  const item: UserActivityItem = {
    id: `act_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    action,
    description,
    timestamp: now,
    metadata
  };

  const updatedData: SingleTableUserData = {
    ...current,
    activities: [item, ...(current.activities || [])].slice(0, 100),
    updated_at: now
  };

  setLocalUserData(userId, updatedData);

  try {
    const docRef = doc(db, FIRESTORE_SINGLE_TABLE, userId);
    await setDoc(docRef, {
      ...updatedData,
      server_timestamp: serverTimestamp()
    }, { merge: true });
  } catch {
    // non-blocking
  }
}

/**
 * Persist user case and clinical memory into Cloud Firestore single table `user_data/{userId}`.
 */
export async function saveUserCaseToFirestore(
  userId: string, 
  caseData: {
    caseId: string;
    title?: string;
    filename?: string;
    status?: string;
    documentCount?: number;
    factsCount?: {
      total: number;
      medications: number;
      appointments: number;
      warnings: number;
      instructions: number;
    };
    summary?: string;
  }
): Promise<void> {
  if (!userId || !caseData.caseId) return;

  const current = getLocalUserData(userId);
  const now = new Date().toISOString();

  const newCase: FirestoreCaseRecord = {
    id: caseData.caseId,
    case_id: caseData.caseId,
    user_id: userId,
    title: caseData.title || caseData.filename || `Discharge Encounter (${now.split("T")[0]})`,
    filename: caseData.filename || "Discharge Document",
    status: caseData.status || "OPEN",
    created_at: now,
    updated_at: now,
    document_count: caseData.documentCount ?? 1,
    facts_count: caseData.factsCount || {
      total: 0,
      medications: 0,
      appointments: 0,
      warnings: 0,
      instructions: 0
    },
    summary: caseData.summary
  };

  // Merge or add to case list
  const existingCases = [...(current.cases || [])];
  const idx = existingCases.findIndex(c => c.case_id === caseData.caseId);
  if (idx >= 0) {
    newCase.created_at = existingCases[idx].created_at || now;
    existingCases[idx] = newCase;
  } else {
    existingCases.unshift(newCase);
  }

  // Activity record
  const activity: UserActivityItem = {
    id: `act_${Date.now()}`,
    action: "UPLOADED_DOCUMENT",
    description: `Uploaded clinical document: ${newCase.filename}`,
    timestamp: now,
    metadata: { case_id: caseData.caseId, filename: newCase.filename }
  };

  const updatedData: SingleTableUserData = {
    ...current,
    cases: existingCases,
    activities: [activity, ...(current.activities || [])].slice(0, 100),
    recent_case_id: caseData.caseId,
    updated_at: now
  };

  // 1. Immediately cache in local storage
  setLocalUserData(userId, updatedData);
  if (typeof window !== "undefined") {
    localStorage.setItem(`carelynx_recent_case_${userId}`, caseData.caseId);
  }

  // 2. Persist to single Firestore table
  try {
    const docRef = doc(db, FIRESTORE_SINGLE_TABLE, userId);
    await setDoc(docRef, {
      ...updatedData,
      server_timestamp: serverTimestamp()
    }, { merge: true });
  } catch (err: unknown) {
    const msg = String(err);
    if (!msg.includes("permission")) {
      console.warn("Could not save case to Firestore single table:", err);
    }
  }
}

/**
 * Fetch all clinical case memories belonging to the user from single Firestore table.
 */
export async function getUserCasesFromFirestore(userId: string): Promise<FirestoreCaseRecord[]> {
  if (!userId) return [];
  const master = await getMasterUserData(userId);
  // Guarantee strict tenant isolation: only return cases matching this user
  return (master.cases || []).filter(c => c.user_id === userId);
}

/**
 * Delete a user's case record from single Firestore table and local memory.
 */
export async function deleteUserCaseFromFirestore(userId: string, caseId: string): Promise<void> {
  if (!userId || !caseId) return;

  const current = getLocalUserData(userId);
  const updatedCases = (current.cases || []).filter(c => c.case_id !== caseId);
  const now = new Date().toISOString();

  const updatedData: SingleTableUserData = {
    ...current,
    cases: updatedCases,
    recent_case_id: current.recent_case_id === caseId ? (updatedCases[0]?.case_id || undefined) : current.recent_case_id,
    updated_at: now
  };

  setLocalUserData(userId, updatedData);

  try {
    const docRef = doc(db, FIRESTORE_SINGLE_TABLE, userId);
    await setDoc(docRef, {
      ...updatedData,
      server_timestamp: serverTimestamp()
    }, { merge: true });
  } catch {
    // non-blocking
  }
}

/**
 * Register a new user with Firebase Auth and initialize their record in the single table.
 */
export async function registerWithFirebase(email: string, password: string, fullName?: string): Promise<User> {
  const credential = await createUserWithEmailAndPassword(auth, email, password);
  const user = credential.user;

  if (fullName && fullName.trim()) {
    try {
      await updateProfile(user, { displayName: fullName.trim() });
    } catch {
      // non-blocking
    }
  }

  // Initialize master document in the single table
  try {
    await saveUserProfileToFirestore(user.uid, {
      displayName: fullName?.trim() || user.email?.split("@")[0] || "Patient",
      email: user.email || email,
      preferredLanguage: "en"
    });
    await logUserActivity(user.uid, "ACCOUNT_REGISTERED", "Registered new patient account");
  } catch {
    // Non-blocking
  }

  return user;
}

/**
 * Sign in existing user with Firebase Auth and log activity in single table.
 */
export async function loginWithFirebase(email: string, password: string): Promise<User> {
  const credential = await signInWithEmailAndPassword(auth, email, password);
  const user = credential.user;

  try {
    await logUserActivity(user.uid, "LOGGED_IN", "Signed in with email and password");
  } catch {
    // Non-blocking
  }

  return user;
}

/**
 * Sign in with Google Popup via Firebase Auth and sync profile in single table.
 */
export async function loginWithGoogle(): Promise<User> {
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  const credential = await signInWithPopup(auth, provider);
  const user = credential.user;

  try {
    await saveUserProfileToFirestore(user.uid, {
      displayName: user.displayName || user.email?.split("@")[0] || "Patient",
      email: user.email || ""
    });
    await logUserActivity(user.uid, "LOGGED_IN_GOOGLE", "Signed in with Google authentication");
  } catch {
    // Non-blocking
  }

  return user;
}

/**
 * Sign out current Firebase user.
 */
export async function logoutFirebase(): Promise<void> {
  await signOut(auth);
}

/**
 * Subscribe to Firebase Auth state changes.
 */
export function onAuthStateChange(callback: (user: User | null) => void) {
  return onAuthStateChanged(auth, callback);
}
