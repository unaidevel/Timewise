import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Sparkles, Users } from "lucide-react";
import { describe, expect, it, vi } from "vitest";
import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(<EmptyState title="No employees" description="Add the first one." />);

    expect(screen.getByRole("heading", { name: "No employees" })).toBeTruthy();
    expect(screen.getByText("Add the first one.")).toBeTruthy();
  });

  it("renders the default Sparkles icon when none is provided", () => {
    const { container } = render(<EmptyState title="t" description="d" />);

    expect(container.querySelector("svg.lucide-sparkles")).toBeTruthy();
  });

  it("renders a custom icon when provided", () => {
    const { container } = render(<EmptyState title="t" description="d" icon={Users} />);

    expect(container.querySelector("svg.lucide-users")).toBeTruthy();
    expect(container.querySelector("svg.lucide-sparkles")).toBeNull();
  });

  it("does not render an action area when no action is passed", () => {
    render(<EmptyState title="t" description="d" />);

    expect(screen.queryByRole("button")).toBeNull();
  });

  it("renders the action node and forwards interactions", async () => {
    const onClick = vi.fn();
    render(
      <EmptyState
        title="t"
        description="d"
        icon={Sparkles}
        action={
          <button type="button" onClick={onClick}>
            Load data
          </button>
        }
      />,
    );

    const btn = screen.getByRole("button", { name: "Load data" });
    await userEvent.click(btn);

    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
