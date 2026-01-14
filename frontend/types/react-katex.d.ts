declare module 'react-katex' {
  import { ComponentType } from 'react';

  export interface InlineMathProps {
    math: string;
    errorColor?: string;
    renderError?: (error: Error) => React.ReactNode;
  }

  export interface BlockMathProps {
    math: string;
    errorColor?: string;
    renderError?: (error: Error) => React.ReactNode;
  }

  export const InlineMath: ComponentType<InlineMathProps>;
  export const BlockMath: ComponentType<BlockMathProps>;
}

