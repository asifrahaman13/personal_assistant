const formatTime = (dateString: string | Date) => {
  console.log(dateString);
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return String(dateString);
    }

    const istDate = new Date(date.getTime() + 5.5 * 60 * 60 * 1000);

    return istDate.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  } catch (error) {
    console.log(error);
    return String(dateString);
  }
};

export { formatTime };
