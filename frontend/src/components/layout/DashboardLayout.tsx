interface DashboardLayoutProps {
  children: React.ReactNode;
}

function DashboardLayout({ children }: DashboardLayoutProps) {
  return <div>{children}</div>;
}

export default DashboardLayout;