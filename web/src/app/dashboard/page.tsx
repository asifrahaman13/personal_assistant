'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { backend_url } from '@/config/config';
import { motion } from 'framer-motion';
import Link from 'next/link';
import LoadingDashboard from '@/components/LoadingDashboard';

interface Group {
  id: number;
  title: string;
  username?: string;
  participants_count: number;
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().slice(0, 10));
  const router = useRouter();
  const [bgTaskStatus, setBgTaskStatus] = useState<string | null>(null);
  const [bgTaskLoading, setBgTaskLoading] = useState(false);
  const [bgTaskError, setBgTaskError] = useState('');

  const [bgEmTaskStatus, setBgEmTaskStatus] = useState<string | null>(null);
  const [bgEmTaskLoading, setBgEmTaskLoading] = useState(false);
  const [bgEmTaskError, setBgEmTaskError] = useState('');

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        const phone = localStorage.getItem('telegram_phone');
        const token = localStorage.getItem('org_jwt');
        const res = await axios.post(
          `${backend_url}/api/v1/groups`,
          {
            phone,
          },
          token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
        );
        setGroups(res.data.groups);
        setSelectedGroup(res.data.groups[0] || null);
        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch groups:', err);
        router.push('/organization');
      }
    };
    fetchGroups();
  }, [router]);

  const handleLogout = async () => {
    try {
      const phone = localStorage.getItem('telegram_phone');
      const organization_id = localStorage.getItem('organization_id');
      const res = await axios.get(`${backend_url}/api/v1/logout/${organization_id}/${phone}`);
      console.log(res.data);

      localStorage.removeItem('telegram_phone');
      localStorage.removeItem('organization_id');
      localStorage.removeItem('org_jwt');

      router.push('/');
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

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

  const startEmailBackgroundTask = async () => {
    setBgEmTaskLoading(true);
    setBgEmTaskError('');
    try {
      const token = localStorage.getItem('org_jwt');
      await axios.post(
        `${backend_url}/api/v1/email-tasks/start`,
        {},
        token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
      );
      setBgEmTaskStatus('Started');
    } catch {
      setBgEmTaskError('Failed to start email task');
    } finally {
      setBgEmTaskLoading(false);
    }
  };

  const stopEmailBackgroundTask = async () => {
    setBgEmTaskLoading(true);
    setBgEmTaskError('');
    try {
      const token = localStorage.getItem('org_jwt');
      await axios.delete(
        `${backend_url}/api/v1/email-tasks/stop`,
        token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
      );
      setBgEmTaskStatus('Stopped');
    } catch {
      setBgEmTaskError('Failed to stop email task');
    } finally {
      setBgEmTaskLoading(false);
    }
  };

  const fetchEmStatus = async () => {
    try {
      const token = localStorage.getItem('org_jwt');
      const response = await axios.get(`${backend_url}/api/v1/email-tasks/status`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 200) {
        setBgEmTaskStatus(response.data.status);
      }
    } catch {
      console.log('Something went wrong');
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
    fetchEmStatus();

    const interval = setInterval(() => {
      fetchTgStatus();
      fetchEmStatus();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <LoadingDashboard />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-gray-100"
      >
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Link
                href="/"
                className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center"
              >
                <svg
                  className="w-6 h-6 text-white"
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
              </Link>
              <div>
                <Link href="/" className="text-2xl font-bold text-gray-900">
                  Personal Assistant
                </Link>
                <p className="text-gray-600">Dashboard</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="px-6 py-2 bg-gradient-to-r from-red-500 to-pink-600 text-white rounded-xl font-semibold hover:shadow-lg hover:scale-105 transition-all duration-200 flex items-center space-x-2 cursor-pointer"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
              <span>Logout</span>
            </button>
          </div>
        </div>
      </motion.header>

      {/* Group Selector */}
      <div className="">
        <div className=" text-xl font-bold py-2  max-w-7xl mx-auto px-6 mt-8">TELEGRAM</div>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-6 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {/* Welcome Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-6"
            >
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mr-4">
                  <svg
                    className="w-6 h-6 text-white"
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
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    {selectedGroup ? selectedGroup.title : 'Welcome!'}
                  </h2>
                  <p className="text-gray-600">
                    {selectedGroup
                      ? `Group ID: ${selectedGroup.id}`
                      : 'You are successfully authenticated'}
                  </p>
                </div>
              </div>
              <p className="text-gray-700">
                {selectedGroup
                  ? `Username: ${selectedGroup.username || 'N/A'}, Participants: ${selectedGroup.participants_count}`
                  : 'Your Telegram account is connected and ready for analysis.'}
              </p>
            </motion.div>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-6"
            >
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>

                {bgTaskStatus && (
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
                  disabled={bgTaskLoading || !selectedGroup}
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
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Statistics</h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded-xl">
                  <span className="text-gray-600">Connected Groups</span>
                  <span className="text-2xl font-bold text-blue-600">{groups.length}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-green-50 rounded-xl">
                  <span className="text-gray-600">Participants</span>
                  <span className="text-2xl font-bold text-green-600">
                    {selectedGroup ? selectedGroup.participants_count : 0}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-purple-50 rounded-xl">
                  <span className="text-gray-600">Username</span>
                  <span className="text-sm text-gray-500">
                    {selectedGroup ? selectedGroup.username || 'N/A' : 'N/A'}
                  </span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </main>
      </div>

      {/* Email selectror */}

      <div className="">
        <div className=" text-xl font-bold py-2  max-w-7xl mx-auto px-6 mt-8">GMAIL</div>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-6 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {/* Welcome Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-6"
            >
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mr-4">
                  <svg
                    className="w-6 h-6 text-white"
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
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    {selectedGroup ? selectedGroup.title : 'Welcome!'}
                  </h2>
                  <p className="text-gray-600">
                    {selectedGroup
                      ? `Group ID: ${selectedGroup.id}`
                      : 'You are successfully authenticated'}
                  </p>
                </div>
              </div>
              <p className="text-gray-700">
                {selectedGroup
                  ? `Username: ${selectedGroup.username || 'N/A'}, Participants: ${selectedGroup.participants_count}`
                  : 'Your Telegram account is connected and ready for analysis.'}
              </p>
            </motion.div>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 p-6"
            >
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>

                {bgEmTaskStatus === null ? (
                  <span className="text-gray-500 text-sm italic">no event</span>
                ) : (
                  <span
                    className={`
        px-3 py-1 rounded-full text-sm font-medium capitalize
        ${
          bgEmTaskStatus === 'running'
            ? 'bg-green-100 text-green-700 border border-green-300'
            : bgEmTaskStatus === 'started'
              ? 'bg-blue-100 text-blue-700 border border-blue-300'
              : bgEmTaskStatus === 'stopped'
                ? 'bg-red-100 text-red-700 border border-red-300'
                : 'bg-gray-100 text-gray-600 border border-gray-300'
        }
      `}
                  >
                    {bgEmTaskStatus}
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
                  disabled={bgEmTaskLoading}
                  onClick={startEmailBackgroundTask}
                >
                  {bgEmTaskLoading ? (
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
                      <span>Processing... {} </span>
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
                  onClick={stopEmailBackgroundTask}
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

                {bgEmTaskError && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700"
                  >
                    {bgEmTaskError}
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
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Statistics</h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded-xl">
                  <span className="text-gray-600">Connected Groups</span>
                  <span className="text-2xl font-bold text-blue-600">{groups.length}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-green-50 rounded-xl">
                  <span className="text-gray-600">Participants</span>
                  <span className="text-2xl font-bold text-green-600">
                    {selectedGroup ? selectedGroup.participants_count : 0}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-purple-50 rounded-xl">
                  <span className="text-gray-600">Username</span>
                  <span className="text-sm text-gray-500">
                    {selectedGroup ? selectedGroup.username || 'N/A' : 'N/A'}
                  </span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </main>
      </div>
    </div>
  );
}
