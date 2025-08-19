'use client';
import { useRouter, usePathname } from 'next/navigation';
import axios from 'axios';
import { backend_url } from '@/config/config';
import { motion } from 'framer-motion';
import Link from 'next/link';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = async () => {
    try {
      const phone = localStorage.getItem('telegram_phone');
      const organization_id = localStorage.getItem('organization_id');
      const res = await axios.get(`${backend_url}/api/v1/logout/${organization_id}/${phone}`);
      console.log(res.data);
      if (res.status === 200) {
        localStorage.clear();
      }
      router.push('/');
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  const linkClasses = (href: string) =>
    `relative text-lg font-medium px-1 pb-1 transition-colors duration-200
   ${
     pathname.startsWith(href)
       ? "text-black font-bold after:content-[''] after:absolute after:left-0 after:bottom-0 after:h-[2px] after:w-full after:bg-black"
       : 'text-gray-500 hover:text-gray-800'
   }
   no-underline focus:outline-none focus:ring-0 active:outline-none active:ring-0`;

  return (
    <div className="min-h-screen flex flex-col items-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-white/80 backdrop-blur-sm shadow-sm border-b w-full border-gray-100"
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

      <div className="flex max-w-7xl  w-full gap-6 px-20 py-4">
        <Link href="/dashboard/rag" className={linkClasses('/dashboard/rag')}>
          RAG
        </Link>
        <Link href="/dashboard/integrations" className={linkClasses('/dashboard/integrations')}>
          Integrations
        </Link>
      </div>

      {children}
    </div>
  );
}
