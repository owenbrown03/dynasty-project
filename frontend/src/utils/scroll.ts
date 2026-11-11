export function scrollToPageTop(behavior: ScrollBehavior = 'auto'): void {
  if (typeof window === 'undefined') {
    return;
  }

  const performScroll = () => {
    try {
      if (typeof window.scrollTo === 'function') {
        window.scrollTo({ top: 0, left: 0, behavior });
      }
    } catch {
      window.scrollTo(0, 0);
    }

    try {
      if (typeof document !== 'undefined') {
        if (typeof document.documentElement?.scrollTo === 'function') {
          document.documentElement.scrollTo({ top: 0, left: 0, behavior });
        }
        if (typeof document.body?.scrollTo === 'function') {
          document.body.scrollTo({ top: 0, left: 0, behavior });
        }
        const content = document.querySelector('main.content');
        if (content && typeof content.scrollTo === 'function') {
          content.scrollTo({ top: 0, left: 0, behavior });
        }
      }
    } catch {
      // Ignore environments where element scrollTo is unsupported
    }
  };

  performScroll();

  if (typeof requestAnimationFrame === 'function') {
    requestAnimationFrame(performScroll);
  }
}
