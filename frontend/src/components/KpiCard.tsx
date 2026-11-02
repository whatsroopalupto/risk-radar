interface KpiCardProps {
  label: string;
  value: string;
  description: string;
  tone?: "high" | "medium" | "default";
}

function KpiCard({
  label,
  value,
  description,
  tone = "default",
}: KpiCardProps) {
  return (
    <div className="kpi-card">
      <div className="kpi-label">{label}</div>

      <div className={`kpi-value kpi-${tone}`}>
        {value}
      </div>

      <div className="kpi-description">{description}</div>
    </div>
  );
}

export default KpiCard;