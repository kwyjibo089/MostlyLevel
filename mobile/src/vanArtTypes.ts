/** Types of the generated camper drawings in vanArt.ts. */

type Paint = {
  /** A fixed fill; absent when the shape takes the body colour. */
  fill?: string;
  body?: boolean;
  stroke?: string;
  sw?: number;
  lc?: 'round';
  op?: number;
};

export type ArtShape =
  | ({ t: 'path'; d: string } & Paint)
  | ({ t: 'rect'; x: number; y: number; w: number; h: number; rx: number } & Paint)
  | ({ t: 'circle'; cx: number; cy: number; r: number } & Paint)
  | ({ t: 'ellipse'; cx: number; cy: number; rx: number; ry: number } & Paint);

export type ArtGradient = {
  kind: 'linear' | 'radial';
  id: string;
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
  cx?: number;
  cy?: number;
  r?: number;
  /** [offset, colour, opacity] */
  stops: [number, string, number][];
};

export type CamperMeta = {
  length: number;
  /** Height including roof parts. */
  height: number;
  width: number;
  /** Rear and front axle positions along the side view. */
  axles: [number, number];
  wheel: number;
  /** Distance between the left and right tyre centres. */
  track: number;
};

export type CamperArt = {
  meta: CamperMeta;
  side: ArtShape[];
  sideShadow: ArtShape | null;
  rear: ArtShape[];
  rearShadow: ArtShape | null;
  top: ArtShape[];
};
