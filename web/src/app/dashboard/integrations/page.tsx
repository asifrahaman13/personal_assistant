import EmailComponent from '@/components/EmailComponent';
import TelegramComponent from '@/components/TelegramComponent';
import React from 'react';

const Page = () => {
  return (
    <div>
      <TelegramComponent />
      <EmailComponent />
    </div>
  );
};

export default Page;
