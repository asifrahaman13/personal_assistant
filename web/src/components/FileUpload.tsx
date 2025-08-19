'use client';

import axios from 'axios';
import { useState } from 'react';
import { backend_url } from '@/config/config';

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('org_jwt');
      const res = await axios.post(`${backend_url}/api/v1/uploads/upload-file/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`,
        },
      });

      setMessage(`✅ ${res.data.message}: ${res.data.filename}`);
    } catch {
      console.error('Something went wrong while uploading the file.');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center  p-6 bg-gray-100">
      <div className="bg-white shadow-lg rounded-2xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4 text-center">Upload a File</h2>
        <input
          type="file"
          onChange={handleFileChange}
          className="mb-4 w-full text-sm text-gray-700"
        />
        <button
          onClick={handleUpload}
          className="w-full bg-blue-600 text-white py-2 rounded-xl hover:bg-blue-700 transition"
        >
          Upload
        </button>
        {message && <p className="mt-4 text-center text-sm text-gray-800">{message}</p>}
      </div>
    </div>
  );
}
