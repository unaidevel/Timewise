import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { downloadCsv } from "./csv";

type AnchorSpy = {
  href: string;
  download: string;
  click: ReturnType<typeof vi.fn>;
};

function captureBlob() {
  const blobs: { type: string; text: string }[] = [];
  const originalBlob = globalThis.Blob;
  class StubBlob {
    type: string;
    constructor(parts: BlobPart[], options?: BlobPropertyBag) {
      this.type = options?.type ?? "";
      blobs.push({
        type: this.type,
        text: parts.map((p) => String(p)).join(""),
      });
    }
  }
  // @ts-expect-error - stubbing global
  globalThis.Blob = StubBlob;
  return {
    blobs,
    restore: () => {
      globalThis.Blob = originalBlob;
    },
  };
}

describe("downloadCsv", () => {
  let anchor: AnchorSpy;
  let createElementSpy: ReturnType<typeof vi.spyOn>;
  let createObjectURLSpy: ReturnType<typeof vi.spyOn>;
  let revokeObjectURLSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    anchor = { href: "", download: "", click: vi.fn() };
    createElementSpy = vi
      .spyOn(document, "createElement")
      .mockImplementation(() => anchor as unknown as HTMLAnchorElement);
    if (!("createObjectURL" in URL)) {
      Object.defineProperty(URL, "createObjectURL", { value: () => "", configurable: true });
    }
    if (!("revokeObjectURL" in URL)) {
      Object.defineProperty(URL, "revokeObjectURL", { value: () => undefined, configurable: true });
    }
    createObjectURLSpy = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:fake");
    revokeObjectURLSpy = vi.spyOn(URL, "revokeObjectURL").mockReturnValue(undefined);
  });

  afterEach(() => {
    createElementSpy.mockRestore();
    createObjectURLSpy.mockRestore();
    revokeObjectURLSpy.mockRestore();
  });

  it("no-ops when rows is empty", () => {
    downloadCsv("empty.csv", []);
    expect(anchor.click).not.toHaveBeenCalled();
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("emits a header row and data rows separated by newlines", () => {
    const capture = captureBlob();
    try {
      downloadCsv("data.csv", [
        { Name: "Maya", Hours: 8 },
        { Name: "James", Hours: 7.5 },
      ]);
      expect(capture.blobs).toHaveLength(1);
      expect(capture.blobs[0].text).toBe("Name,Hours\nMaya,8\nJames,7.5");
      expect(capture.blobs[0].type).toBe("text/csv;charset=utf-8");
    } finally {
      capture.restore();
    }
  });

  it("quotes and escapes values that contain commas, quotes or newlines", () => {
    const capture = captureBlob();
    try {
      downloadCsv("escaped.csv", [
        { Name: "Smith, John", Note: 'He said "hi"' },
        { Name: "Plain", Note: "line\nbreak" },
      ]);
      expect(capture.blobs[0].text).toBe(
        'Name,Note\n"Smith, John","He said ""hi"""\nPlain,"line\nbreak"',
      );
    } finally {
      capture.restore();
    }
  });

  it("triggers a download via an anchor element with the given filename", () => {
    downloadCsv("payroll.csv", [{ Total: 100 }]);
    expect(createElementSpy).toHaveBeenCalledWith("a");
    expect(anchor.href).toBe("blob:fake");
    expect(anchor.download).toBe("payroll.csv");
    expect(anchor.click).toHaveBeenCalledTimes(1);
    expect(revokeObjectURLSpy).toHaveBeenCalledWith("blob:fake");
  });
});
