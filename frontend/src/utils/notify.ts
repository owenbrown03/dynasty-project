import toast from 'react-hot-toast';

export const notify = {
  success: (msg: string) => toast.success(msg),

  error: (msg: string) => toast.error(msg),

  loading: (msg: string) => toast.loading(msg),

  dismiss: (id?: string) => {
    toast.dismiss(id);
  },

  promise: <T>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string;
      error: string;
    }
  ) => {
    return toast.promise(promise, messages);
  },
};