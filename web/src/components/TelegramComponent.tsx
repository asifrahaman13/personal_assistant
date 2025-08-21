'use client';

import { backend_url } from '@/config/config';
import axios from 'axios';
import { motion } from 'framer-motion';
import React, { useEffect, useState } from 'react';
import { fetchStatusInterval } from '@/config/config';

export type EmailStats = {
  success: boolean;
  total_messages: number;
  unique_senders: number;
  replies_sent: number;
  date_range: {
    start: string | null;
    end: string | null;
  };
};

const TelegramComponent = () => {
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().slice(0, 10));

  const [bgTaskStatus, setBgTaskStatus] = useState<string | null>(null);
  const [bgTaskLoading, setBgTaskLoading] = useState(false);
  const [bgTaskError, setBgTaskError] = useState('');
  const [tgStats, setTgStats] = useState<EmailStats | null>(null);

  const fetchTgStats = async () => {
    try {
      const token = localStorage.getItem('org_jwt');
      const response = await axios.get(`${backend_url}/api/v1/background-tasks/stats`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.status === 200) {
        setTgStats(response.data);
      }
    } catch {
      setTgStats(null);
    }
  };

  useEffect(() => {
    fetchTgStats();
  }, []);

  const startBackgroundTask = async () => {
    setBgTaskLoading(true);
    setBgTaskError('');
    try {
      const token = localStorage.getItem('org_jwt');
      await axios.post(
        `${backend_url}/api/v1/background-tasks/start`,
        {},
        token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
      );
      setBgTaskStatus('Started');
    } catch {
      setBgTaskError('Failed to start background task');
    } finally {
      setBgTaskLoading(false);
    }
  };

  const stopBackgroundTask = async () => {
    setBgTaskLoading(true);
    setBgTaskError('');
    try {
      const token = localStorage.getItem('org_jwt');
      await axios.delete(
        `${backend_url}/api/v1/background-tasks/stop`,
        token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
      );
      setBgTaskStatus('Stopped');
    } catch {
      setBgTaskError('Failed to stop background task');
    } finally {
      setBgTaskLoading(false);
    }
  };

  const fetchTgStatus = async () => {
    try {
      const token = localStorage.getItem('org_jwt');
      const response = await axios.get(`${backend_url}/api/v1/background-tasks/status`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 200) {
        console.log(response.data);
        setBgTaskStatus(response.data.status);
      }
    } catch {
      console.log('Something went wrong');
    }
  };

  useEffect(() => {
    fetchTgStatus();
    const fetchStatusAsync = async () => {
      try {
        Promise.all([fetchTgStatus()]);
      } catch {
        console.error('Sorry unable to update the status update.');
      }
    };
    const interval = setInterval(() => {
      fetchStatusAsync();
    }, fetchStatusInterval);

    return () => clearInterval(interval);
  }, []);

  return (
    <React.Fragment>
      {/* Group Selector */}
      <div className="">
        <div className=" text-xl font-bold max-w-8xl ">TELEGRAM</div>

        {/* Main Content */}
        <main className="max-w-8xl py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-6"
            >
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>

                {bgTaskStatus === null ? (
                  <span className="text-gray-500 text-sm italic">no event</span>
                ) : (
                  <span
                    className={`
        px-3 py-1 rounded-full text-sm font-medium
        ${
          bgTaskStatus === 'running'
            ? 'bg-green-100 text-green-700 border border-green-300'
            : bgTaskStatus === 'started'
              ? 'bg-blue-100 text-blue-700 border border-blue-300'
              : bgTaskStatus === 'stopped'
                ? 'bg-red-100 text-red-700 border border-red-300'
                : 'bg-gray-100 text-gray-600 border border-gray-300'
        }
      `}
                  >
                    {bgTaskStatus}
                  </span>
                )}
              </div>

              <div className="space-y-4">
                {/* Date range pickers */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={startDate}
                      max={endDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                    <input
                      type="date"
                      value={endDate}
                      min={startDate}
                      max={new Date().toISOString().slice(0, 10)}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
                    />
                  </div>
                </div>
                <button
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 px-4 rounded-xl font-semibold hover:shadow-lg hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 cursor-pointer"
                  disabled={bgTaskLoading}
                  onClick={startBackgroundTask}
                >
                  {bgTaskLoading ? (
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
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                        />
                      </svg>
                      <span>Start process</span>
                    </>
                  )}
                </button>

                <button
                  className="w-full bg-red-600 backdrop-blur-sm text-white border border-gray-200 py-3 px-4 rounded-xl font-semibold hover:scale-105 hover:shadow-lg transition-all duration-200 flex items-center justify-center space-x-2 cursor-pointer"
                  onClick={stopBackgroundTask}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  <span>stop process</span>
                </button>

                <button className="w-full bg-white/80 backdrop-blur-sm text-gray-700 border border-gray-200 py-3 px-4 rounded-xl font-semibold hover:bg-white hover:shadow-lg transition-all duration-200 flex items-center justify-center space-x-2 cursor-pointer">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  <span>Settings</span>
                </button>

                {bgTaskError && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700"
                  >
                    {bgTaskError}
                  </motion.div>
                )}
              </div>
            </motion.div>

            {/* Stats */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-6"
            ></motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-6"
            >
              <h2 className="text-lg font-bold mb-4">Telegram Stats</h2>
              {tgStats ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex flex-col items-center bg-blue-50 rounded-xl p-4 shadow">
                    <svg
                      className="w-8 h-8 text-blue-500 mb-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 8h10M7 12h6m-6 4h10"
                      />
                    </svg>
                    <span className="text-2xl font-bold text-blue-700">
                      {tgStats.total_messages}
                    </span>
                    <span className="text-sm text-gray-500">Total Messages</span>
                  </div>
                  <div className="flex flex-col items-center bg-green-50 rounded-xl p-4 shadow">
                    <svg
                      className="w-8 h-8 text-green-500 mb-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87M12 4a4 4 0 110 8 4 4 0 010-8z"
                      />
                    </svg>
                    <span className="text-2xl font-bold text-green-700">
                      {tgStats.unique_senders}
                    </span>
                    <span className="text-sm text-gray-500">Unique Senders</span>
                  </div>
                  <div className="flex flex-col items-center bg-purple-50 rounded-xl p-4 shadow">
                    <svg
                      className="w-8 h-8 text-purple-500 mb-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 8h2a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2v-8a2 2 0 012-2h2"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 12v4m0 0l-2-2m2 2l2-2"
                      />
                    </svg>
                    <span className="text-2xl font-bold text-purple-700">
                      {tgStats.replies_sent}
                    </span>
                    <span className="text-sm text-gray-500">Replies Sent</span>
                  </div>
                </div>
              ) : (
                <span className="text-gray-500">No stats available</span>
              )}
            </motion.div>
          </motion.div>
        </main>
      </div>
    </React.Fragment>
  );
};

export default TelegramComponent;
