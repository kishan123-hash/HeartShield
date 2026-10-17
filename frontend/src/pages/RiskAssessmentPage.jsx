import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Heart,
  Scale,
  Sparkles
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../api/client';

export default function RiskAssessmentPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const navigate = useNavigate();

  // Form State
  const [formData, setFormData] = useState({
    // Step 1: Basic Info
    age: 45,
    gender: 'male',
    height_cm: 170,
    weight_kg: 72,
    bmi: 24.9,

    // Step 2: Vitals & Lab
    systolic_bp: 120,
    diastolic_bp: 80,
    heart_rate: 72,
    blood_glucose: 95,
    total_cholesterol: 180,
    hdl: 50,
    ldl: 100,
    diabetes: false,
    hypertension: false,
    previous_heart_disease: false,
    family_history: false,

    // Step 3: Lifestyle
    smoking: 'Never',
    alcohol: 'Never',
    physical_activity: 'Moderate',
    exercise_frequency: '3–4 days/week',
    diet: 'Balanced',
    sleep_duration: '7–8 hours',
    sleep_quality: 'Good',
    stress_level: 'Low',
    sedentary_time: '2–4 hours',
  });

  // Auto calculate BMI when height or weight change
  useEffect(() => {
    const h = Number(formData.height_cm) / 100;
    const w = Number(formData.weight_kg);
    if (h > 0 && w > 0) {
      const calculatedBmi = Number((w / (h * h)).toFixed(1));
      setFormData((prev) => ({ ...prev, bmi: calculatedBmi }));
    }
  }, [formData.height_cm, formData.weight_kg]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleNext = () => {
    setError('');
    setCurrentStep((prev) => Math.min(prev + 1, 4));
  };

  const handleBack = () => {
    setError('');
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 1. Post assessment to FastAPI
      const payload = {
        systolic_bp: Number(formData.systolic_bp),
        diastolic_bp: Number(formData.diastolic_bp),
        heart_rate: Number(formData.heart_rate),
        total_cholesterol: Number(formData.total_cholesterol),
        hdl: Number(formData.hdl),
        ldl: Number(formData.ldl),
        blood_glucose: Number(formData.blood_glucose),
        bmi: Number(formData.bmi),
        diabetes: Boolean(formData.diabetes),
        hypertension: Boolean(formData.hypertension),
        previous_heart_disease: Boolean(formData.previous_heart_disease),
        family_history: Boolean(formData.family_history),
        smoking: formData.smoking,
        alcohol: formData.alcohol,
        physical_activity: formData.physical_activity,
        exercise_frequency: formData.exercise_frequency,
        diet: formData.diet,
        sleep_duration: formData.sleep_duration,
        sleep_quality: formData.sleep_quality,
        stress_level: formData.stress_level,
        sedentary_time: formData.sedentary_time,
      };

      const res = await api.post('/assessments/', payload);
      const assessmentId = res.data.id;

      // 2. Fetch the generated prediction
      // The backend auto-generates prediction upon assessment save
      const predRes = await api.get('/predictions/latest');
      const predictionId = predRes.data?.id || assessmentId;

      navigate(`/patient/prediction-result/${predictionId}`);
    }catch (err) {
  console.error('Assessment submission error:', err);
  console.error('HTTP status:', err.response?.status);
  console.error('Backend response:', err.response?.data);

  const detail = err.response?.data?.detail;

  setError(
    typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
      ? detail.map((item) => item.msg).join(', ')
      : err.message || 'Assessment submission failed.'
  );
} finally {
  setLoading(false);
}
  };

  return (
    <div className="min-h-screen flex bg-warm-bg">
      <Sidebar />

      <main className="flex-1 p-6 sm:p-10 max-w-4xl mx-auto space-y-8">
        {/* Header (Screen 12) */}
        <div className="text-center max-w-xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-800 bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
            Clinical & Lifestyle Data
          </span>
          <h1 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
            Heart Risk Assessment
          </h1>
          <p className="text-xs text-warm-muted">
            Please fill in your current vitals and daily habits for our hard-voting AI ensemble.
          </p>
        </div>

        {/* 4-Step Progress Indicator */}
        <div className="bg-white p-4 sm:p-6 rounded-3xl border border-warm-border shadow-xs">
          <div className="flex items-center justify-between max-w-2xl mx-auto">
            {[
              { num: 1, label: 'Basic Info' },
              { num: 2, label: 'Vital Signs' },
              { num: 3, label: 'Lifestyle' },
              { num: 4, label: 'Review' },
            ].map((st, idx) => (
              <React.Fragment key={st.num}>
                <div className="flex flex-col items-center">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-all ${
                      currentStep === st.num
                        ? 'bg-brand-800 text-white shadow-md shadow-brand-900/30'
                        : currentStep > st.num
                        ? 'bg-emerald-600 text-white'
                        : 'bg-warm-bg text-warm-muted border border-warm-border'
                    }`}
                  >
                    {currentStep > st.num ? '✓' : st.num}
                  </div>
                  <span
                    className={`text-[11px] font-semibold mt-1.5 hidden sm:block ${
                      currentStep === st.num ? 'text-brand-800 font-bold' : 'text-warm-muted'
                    }`}
                  >
                    {st.label}
                  </span>
                </div>
                {idx < 3 && (
                  <div
                    className={`flex-1 h-0.5 mx-2 sm:mx-4 transition-all ${
                      currentStep > idx + 1 ? 'bg-emerald-600' : 'bg-warm-border'
                    }`}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Multi-Step Form Card */}
        <div className="bg-white p-6 sm:p-10 rounded-3xl border border-warm-border shadow-xs">
          <form onSubmit={handleSubmit}>
            {/* STEP 1: BASIC INFO */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold text-gray-900 border-b border-warm-border pb-3">
                  Step 1: Basic Demographics & Body Metrics
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Age (Years)
                    </label>
                    <input
                      type="number"
                      required
                      min={18}
                      max={120}
                      value={formData.age}
                      onChange={(e) => handleChange('age', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Gender
                    </label>
                    <select
                      value={formData.gender}
                      onChange={(e) => handleChange('gender', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 bg-white"
                    >
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Height (cm)
                    </label>
                    <input
                      type="number"
                      required
                      min={100}
                      max={250}
                      value={formData.height_cm}
                      onChange={(e) => handleChange('height_cm', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Weight (kg)
                    </label>
                    <input
                      type="number"
                      required
                      min={30}
                      max={300}
                      value={formData.weight_kg}
                      onChange={(e) => handleChange('weight_kg', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>
                </div>

                {/* Auto Calculated BMI Preview */}
                <div className="p-4 rounded-2xl bg-warm-bg/70 border border-warm-border flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Scale className="w-6 h-6 text-brand-800" />
                    <div>
                      <span className="text-xs font-bold text-gray-900">Calculated Body Mass Index (BMI)</span>
                      <p className="text-[11px] text-warm-muted">Computed automatically from height and weight</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xl font-black text-brand-800">{formData.bmi}</span>
                    <span className="text-[10px] block text-warm-muted uppercase font-bold">kg/m²</span>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2: VITAL SIGNS */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold text-gray-900 border-b border-warm-border pb-3">
                  Step 2: Clinical Vitals & Laboratory Values
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Systolic BP (mmHg)
                    </label>
                    <input
                      type="number"
                      required
                      min={60}
                      max={260}
                      value={formData.systolic_bp}
                      onChange={(e) => handleChange('systolic_bp', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Diastolic BP (mmHg)
                    </label>
                    <input
                      type="number"
                      required
                      min={40}
                      max={180}
                      value={formData.diastolic_bp}
                      onChange={(e) => handleChange('diastolic_bp', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Heart Rate (BPM)
                    </label>
                    <input
                      type="number"
                      required
                      min={30}
                      max={220}
                      value={formData.heart_rate}
                      onChange={(e) => handleChange('heart_rate', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Blood Glucose (mg/dL)
                    </label>
                    <input
                      type="number"
                      required
                      min={40}
                      max={500}
                      value={formData.blood_glucose}
                      onChange={(e) => handleChange('blood_glucose', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Total Cholesterol (mg/dL)
                    </label>
                    <input
                      type="number"
                      required
                      min={80}
                      max={450}
                      value={formData.total_cholesterol}
                      onChange={(e) => handleChange('total_cholesterol', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      HDL Cholesterol (mg/dL)
                    </label>
                    <input
                      type="number"
                      required
                      min={15}
                      max={140}
                      value={formData.hdl}
                      onChange={(e) => handleChange('hdl', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800"
                    />
                  </div>
                </div>

                {/* Medical History Toggles */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <label className="flex items-center space-x-3 p-3.5 rounded-2xl bg-warm-bg/60 border border-warm-border cursor-pointer hover:bg-rose-50/50">
                    <input
                      type="checkbox"
                      checked={formData.diabetes}
                      onChange={(e) => handleChange('diabetes', e.target.checked)}
                      className="w-4 h-4 rounded text-brand-800 focus:ring-brand-800"
                    />
                    <span className="text-xs font-semibold text-gray-800">Diagnosed with Diabetes</span>
                  </label>

                  <label className="flex items-center space-x-3 p-3.5 rounded-2xl bg-warm-bg/60 border border-warm-border cursor-pointer hover:bg-rose-50/50">
                    <input
                      type="checkbox"
                      checked={formData.hypertension}
                      onChange={(e) => handleChange('hypertension', e.target.checked)}
                      className="w-4 h-4 rounded text-brand-800 focus:ring-brand-800"
                    />
                    <span className="text-xs font-semibold text-gray-800">Diagnosed with Hypertension</span>
                  </label>

                  <label className="flex items-center space-x-3 p-3.5 rounded-2xl bg-warm-bg/60 border border-warm-border cursor-pointer hover:bg-rose-50/50">
                    <input
                      type="checkbox"
                      checked={formData.previous_heart_disease}
                      onChange={(e) => handleChange('previous_heart_disease', e.target.checked)}
                      className="w-4 h-4 rounded text-brand-800 focus:ring-brand-800"
                    />
                    <span className="text-xs font-semibold text-gray-800">Prior Heart Disease or Stroke</span>
                  </label>

                  <label className="flex items-center space-x-3 p-3.5 rounded-2xl bg-warm-bg/60 border border-warm-border cursor-pointer hover:bg-rose-50/50">
                    <input
                      type="checkbox"
                      checked={formData.family_history}
                      onChange={(e) => handleChange('family_history', e.target.checked)}
                      className="w-4 h-4 rounded text-brand-800 focus:ring-brand-800"
                    />
                    <span className="text-xs font-semibold text-gray-800">Family History of Heart Disease</span>
                  </label>
                </div>
              </div>
            )}

            {/* STEP 3: LIFESTYLE */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold text-gray-900 border-b border-warm-border pb-3">
                  Step 3: Daily Habits & Lifestyle Factors
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Smoking Status
                    </label>
                    <select
                      value={formData.smoking}
                      onChange={(e) => handleChange('smoking', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 bg-white"
                    >
                      <option value="Never">Never Smoked</option>
                      <option value="Former">Former Smoker</option>
                      <option value="Regularly">Current Smoker (Regular)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Alcohol Consumption
                    </label>
                    <select
                      value={formData.alcohol}
                      onChange={(e) => handleChange('alcohol', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 bg-white"
                    >
                      <option value="Never">Never</option>
                      <option value="Occasional">Occasional</option>
                      <option value="Moderate">Moderate</option>
                      <option value="Regularly">Heavy / Regular</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Physical Activity Level
                    </label>
                    <select
                      value={formData.physical_activity}
                      onChange={(e) => handleChange('physical_activity', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 bg-white"
                    >
                      <option value="Active">Active (Intense workout)</option>
                      <option value="Moderate">Moderate (Brisk walk / exercise)</option>
                      <option value="Low">Low (Mostly sedentary)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Sleep Duration
                    </label>
                    <select
                      value={formData.sleep_duration}
                      onChange={(e) => handleChange('sleep_duration', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 bg-white"
                    >
                      <option value="7–8 hours">7–8 hours (Optimal)</option>
                      <option value="6–7 hours">6–7 hours</option>
                      <option value="Less than 5 hours">Less than 5 hours</option>
                      <option value="More than 9 hours">More than 9 hours</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Stress Level
                    </label>
                    <select
                      value={formData.stress_level}
                      onChange={(e) => handleChange('stress_level', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 bg-white"
                    >
                      <option value="Low">Low</option>
                      <option value="Moderate">Moderate</option>
                      <option value="High">High</option>
                      <option value="Very High">Very High</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Sedentary Time
                    </label>
                    <select
                      value={formData.sedentary_time}
                      onChange={(e) => handleChange('sedentary_time', e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-warm-border text-sm focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 bg-white"
                    >
                      <option value="2–4 hours">2–4 hours/day</option>
                      <option value="4–6 hours/day">4–6 hours/day</option>
                      <option value="More than 8 hours/day">More than 8 hours/day</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 4: REVIEW & CONFIRM */}
            {currentStep === 4 && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold text-gray-900 border-b border-warm-border pb-3">
                  Step 4: Review Your Information
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="p-4 rounded-2xl bg-warm-bg/60 border border-warm-border space-y-2">
                    <span className="font-bold text-brand-800 uppercase tracking-wider block">Demographics</span>
                    <p><span className="text-warm-muted">Age:</span> {formData.age} yrs</p>
                    <p><span className="text-warm-muted">Gender:</span> {formData.gender}</p>
                    <p><span className="text-warm-muted">BMI:</span> {formData.bmi} kg/m²</p>
                  </div>

                  <div className="p-4 rounded-2xl bg-warm-bg/60 border border-warm-border space-y-2">
                    <span className="font-bold text-brand-800 uppercase tracking-wider block">Vitals</span>
                    <p><span className="text-warm-muted">Blood Pressure:</span> {formData.systolic_bp}/{formData.diastolic_bp} mmHg</p>
                    <p><span className="text-warm-muted">Heart Rate:</span> {formData.heart_rate} bpm</p>
                    <p><span className="text-warm-muted">Cholesterol:</span> {formData.total_cholesterol} mg/dL</p>
                    <p><span className="text-warm-muted">Glucose:</span> {formData.blood_glucose} mg/dL</p>
                  </div>

                  <div className="p-4 rounded-2xl bg-warm-bg/60 border border-warm-border space-y-2">
                    <span className="font-bold text-brand-800 uppercase tracking-wider block">Lifestyle</span>
                    <p><span className="text-warm-muted">Smoking:</span> {formData.smoking}</p>
                    <p><span className="text-warm-muted">Activity:</span> {formData.physical_activity}</p>
                    <p><span className="text-warm-muted">Sleep:</span> {formData.sleep_duration}</p>
                    <p><span className="text-warm-muted">Stress:</span> {formData.stress_level}</p>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-brand-50/60 border border-brand-200 text-xs text-brand-900 leading-relaxed">
                  Upon submission, the <strong>HeartShield Hard-Voting Ensemble</strong> (Logistic Regression + Random Forest + XGBoost) will evaluate your clinical factors and calculate explainable SHAP contribution scores.
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between pt-8 border-t border-warm-border mt-8">
              {currentStep > 1 ? (
                <button
                  type="button"
                  onClick={handleBack}
                  className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-full text-xs font-bold text-gray-700 bg-warm-bg hover:bg-warm-border transition-all"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
              ) : (
                <div></div>
              )}

              {currentStep < 4 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="inline-flex items-center space-x-2 px-8 py-3 rounded-full text-xs font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-md shadow-brand-900/20 transition-all"
                >
                  <span>Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center space-x-2 px-10 py-3.5 rounded-full text-sm font-bold text-white bg-brand-800 hover:bg-brand-900 shadow-lg shadow-brand-900/30 transition-all disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{loading ? 'Evaluating Model...' : 'Calculate Prediction'}</span>
                </button>
              )}
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
