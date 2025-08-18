'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { backend_url } from '@/config/config';
import { motion } from 'framer-motion';

interface LoginResponse {
  success: boolean;
  message: string;
  requires_code: boolean;
}

interface CodeResponse {
  success: boolean;
  message: string;
  session_id?: string;
}

export function TelegramAuth() {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState<'phone' | 'code' | 'success' | 'error'>('phone');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [checkingSession, setCheckingSession] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const checkExistingSession = async () => {
      try {
        const storedPhone = localStorage.getItem('telegram_phone');
        const token = localStorage.getItem('org_jwt');
        if (storedPhone) {
          const response = await axios.post<LoginResponse>(
            `${backend_url}/api/v1/telegram-login`,
            { phone: storedPhone },
            token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
          );

          if (response.data) {
            router.push('/dashboard');
            return;
          }
        }
      } catch (err) {
        console.error('Session check error:', err);
      } finally {
        setCheckingSession(false);
      }
    };

    checkExistingSession();
  }, [router]);

  const handlePhoneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('org_jwt');
      const response = await axios.post<LoginResponse>(
        `${backend_url}/api/v1/telegram-login`,
        { phone },
        token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
      );

      if (response.data.success) {
        if (!response.data.requires_code) {
          localStorage.setItem('telegram_phone', phone);
          router.push('/dashboard');
          return;
        }

        setMessage(response.data.message);
        setStep('code');
      } else {
        setError(response.data.message);
        setStep('error');
      }
    } catch {
      setError('Sorry not able to authenticate');
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const handleCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('org_jwt');
      const response = await axios.post<CodeResponse>(
        `${backend_url}/api/v1/code`,
        { phone: phone, code: code },
        token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
      );

      if (response.data.success) {
        localStorage.setItem('telegram_phone', phone);
        setMessage(response.data.message);
        setStep('success');

        setTimeout(() => {
          router.push('/dashboard');
        }, 2000);
      } else {
        setError(response.data.message);
        setStep('error');
      }
    } catch {
      setError('Sorry not able to authenticate');
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setStep('phone');
    setPhone('');
    setCode('');
    setMessage('');
    setError('');
  };

  if (checkingSession) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-8"
      >
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
            <svg
              className="animate-spin w-8 h-8 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Checking Authentication</h2>
          <p className="text-gray-600">Verifying your session...</p>
        </div>
      </motion.div>
    );
  }

  if (step === 'success') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-8"
      >
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Successful!</h2>
          <p className="text-gray-600 mb-6">{message}</p>
          <div className="flex items-center justify-center space-x-2 text-blue-600">
            <div className="animate-pulse">
              <span className="text-sm font-medium">Redirecting to dashboard...</span>
            </div>
            <svg
              className="w-4 h-4 animate-spin"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </div>
        </div>
      </motion.div>
    );
  }

  if (step === 'error') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-8"
      >
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-pink-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Failed</h2>
          <p className="text-red-600 mb-6">{error}</p>
          <button
            onClick={resetForm}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl font-semibold hover:shadow-lg hover:scale-105 transition-all duration-200"
          >
            Try Again
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-8"
    >
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          {step === 'phone' ? 'Enter Phone Number' : 'Enter Verification Code'}
        </h2>
        <p className="text-gray-600">
          {step === 'phone'
            ? 'We will send a verification code to your Telegram'
            : 'Enter the code sent to your Telegram'}
        </p>
      </div>

      {step === 'phone' ? (
        <form onSubmit={handlePhoneSubmit} className="space-y-6">
          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
              Phone Number
            </label>
            <input
              type="tel"
              id="phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+1234567890"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl font-semibold hover:shadow-lg hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 cursor-pointer"
          >
            {loading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span>Sending Code...</span>
              </>
            ) : (
              <>
                <span>Send Code</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
              </>
            )}
          </button>
        </form>
      ) : (
        <form onSubmit={handleCodeSubmit} className="space-y-6">
          <div>
            <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-2">
              Verification Code
            </label>
            <input
              type="text"
              id="code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="12345"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
              required
            />
          </div>
          <div className="space-y-4">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl font-semibold hover:shadow-lg hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <span>Verify Code</span>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </>
              )}
            </button>
            <button
              type="button"
              onClick={() => setStep('phone')}
              className="w-full bg-gray-600 text-white py-3 rounded-xl font-semibold hover:bg-gray-700 hover:shadow-lg transition-all duration-200 cursor-pointer"
            >
              Back to Phone
            </button>
          </div>
        </form>
      )}

      {message && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-xl text-blue-700"
        >
          <p className="text-sm">{message}</p>
        </motion.div>
      )}
    </motion.div>
  );
}
