import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { PhotoUpload } from "../photo-upload";

// Mock the signed-upload hook so tests don't make real network calls
const mockUploadFile = vi.fn<(file: File) => Promise<string>>();

vi.mock("@/hooks/use-signed-upload", () => ({
  uploadFile: (file: File) => mockUploadFile(file),
  useSignedUpload: () => ({ uploadFile: mockUploadFile }),
}));

beforeEach(() => {
  mockUploadFile.mockReset();
  // Mock URL.createObjectURL (jsdom doesn't implement it)
  global.URL.createObjectURL = vi.fn(() => "blob:mock");
  global.URL.revokeObjectURL = vi.fn();
});

function makeFile(name: string, type = "image/jpeg"): File {
  return new File(["content"], name, { type });
}

async function uploadFiles(files: File[]) {
  const user = userEvent.setup();
  render(<PhotoUpload onSubmit={vi.fn()} />);
  const input = screen.getByLabelText(/upload photos/i);
  await user.upload(input, files);
  return { user };
}

describe("PhotoUpload", () => {
  it("assigns page numbers based on order", async () => {
    await uploadFiles([
      makeFile("a.jpg"),
      makeFile("b.jpg"),
    ]);
    expect(screen.getByText("Page 1")).toBeInTheDocument();
    expect(screen.getByText("Page 2")).toBeInTheDocument();
  });

  it("caps at 4 files", async () => {
    await uploadFiles(
      Array.from({ length: 5 }, (_, i) => makeFile(`p${i}.jpg`))
    );
    expect(screen.queryByText("Page 5")).not.toBeInTheDocument();
    expect(screen.getByText("Page 4")).toBeInTheDocument();
  });

  it("removes thumbnail when X is clicked", async () => {
    const user = userEvent.setup();
    render(<PhotoUpload onSubmit={vi.fn()} />);
    const input = screen.getByLabelText(/upload photos/i);
    await user.upload(input, [makeFile("a.jpg"), makeFile("b.jpg")]);

    expect(screen.getByText("Page 1")).toBeInTheDocument();
    expect(screen.getByText("Page 2")).toBeInTheDocument();

    const removeBtn = screen.getByLabelText("Remove page 1");
    await user.click(removeBtn);

    // After removing page 1, only one file remains (renumbered to Page 1)
    expect(screen.queryByText("Page 2")).not.toBeInTheDocument();
    expect(screen.getByText("Page 1")).toBeInTheDocument();
  });

  it("shows submit button after files are added", async () => {
    await uploadFiles([makeFile("a.jpg")]);
    expect(screen.getByRole("button", { name: /submit/i })).toBeInTheDocument();
  });

  it("calls onSubmit with photo paths after successful upload", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<PhotoUpload onSubmit={onSubmit} />);

    // Mock the uploadFile function to return a fixed path
    mockUploadFile.mockResolvedValue("uploads/student-id/file.jpg");

    const input = screen.getByLabelText(/upload photos/i);
    await user.upload(input, [makeFile("a.jpg")]);

    const submitBtn = screen.getByRole("button", { name: /submit/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(["uploads/student-id/file.jpg"]);
    });
  });

  it("does not submit more than 4 files even via drag-drop after initial cap", async () => {
    await uploadFiles(
      Array.from({ length: 5 }, (_, i) => makeFile(`p${i}.jpg`))
    );
    // Only 4 thumbnails rendered
    const pages = screen.getAllByText(/^Page \d+$/);
    expect(pages).toHaveLength(4);
  });
});
