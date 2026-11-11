import { beforeEach, describe, expect, it, vi } from 'vitest';
import { scrollToPageTop } from './scroll';

describe('scrollToPageTop', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('invokes window, document and main.content scrollTo', () => {
    const windowScrollTo = vi.fn();
    const docElementScrollTo = vi.fn();
    const bodyScrollTo = vi.fn();
    const contentScrollTo = vi.fn();

    vi.stubGlobal('scrollTo', windowScrollTo);
    document.documentElement.scrollTo = docElementScrollTo;
    document.body.scrollTo = bodyScrollTo;

    const main = document.createElement('main');
    main.className = 'content';
    main.scrollTo = contentScrollTo;
    document.body.appendChild(main);

    scrollToPageTop();

    expect(windowScrollTo).toHaveBeenCalledWith({ top: 0, left: 0, behavior: 'auto' });
    expect(docElementScrollTo).toHaveBeenCalledWith({ top: 0, left: 0, behavior: 'auto' });
    expect(bodyScrollTo).toHaveBeenCalledWith({ top: 0, left: 0, behavior: 'auto' });
    expect(contentScrollTo).toHaveBeenCalledWith({ top: 0, left: 0, behavior: 'auto' });

    document.body.removeChild(main);
  });
});
