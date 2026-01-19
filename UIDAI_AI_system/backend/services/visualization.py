import os
from typing import List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def generate_charts(df: pd.DataFrame, charts_output_dir: str, run_id: str, max_charts: int = 5) -> List[str]:
    """Generate charts SAFELY - no crashes if columns missing."""
    os.makedirs(charts_output_dir, exist_ok=True)
    chart_paths = []
    
    # FIXED: Compute totals ONCE at top level
    total_records = len(df)
    total_anomalies = int(df.get('is_anomaly', pd.Series(0)).sum()) if 'is_anomaly' in df.columns else 0
    
    plt.style.use('default')

    try:
        # 1. Safe numeric trend charts (original functionality)
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        exclude_cols = {'anomaly', 'is_anomaly'}
        numeric_cols = [c for c in numeric_cols if c not in exclude_cols][:max_charts]
        
        date_cols = df.select_dtypes(include=['datetime64[ns]']).columns.tolist()
        x_col = date_cols[0] if date_cols else None
        
        for col in numeric_cols:
            chart_path = _safe_trend_chart(df, col, x_col, charts_output_dir, run_id)
            if chart_path: chart_paths.append(chart_path)
            
    except Exception:
        pass

    # 2. Executive charts (safe fallbacks)
    _safe_exec_charts(df, total_records, total_anomalies, charts_output_dir, run_id, chart_paths)
    
    return chart_paths


def _safe_trend_chart(df, col, x_col, charts_output_dir, run_id):
    try:
        plt.figure(figsize=(12, 6))
        x_values = df[x_col] if x_col else range(len(df))
        plt.plot(x_values, df[col], color="steelblue", linewidth=2)
        
        if 'is_anomaly' in df.columns:
            anomalies = df[df['is_anomaly'] == 1]
            if not anomalies.empty:
                plt.scatter(anomalies[x_col] if x_col else range(len(anomalies)), 
                           anomalies[col], color="red", s=50, label="Anomalies")
        
        plt.title(f'{col} with Anomalies')
        plt.tight_layout()
        chart_file = f"{run_id}_{col}_trend.png"
        path = os.path.join(charts_output_dir, chart_file)
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path
    except:
        plt.close()
        return None


def _safe_exec_charts(df, total_records, total_anomalies, charts_output_dir, run_id, chart_paths):
    """Generate 4 executive charts - safe column detection."""
    
    normal_count = total_records - total_anomalies
    
    # 1. Anomaly Volume Over Time (ANY date-like column)
    time_chart = _safe_time_chart(df, charts_output_dir, run_id)
    if time_chart: chart_paths.append(time_chart)
    
    # 2. Top 10 Anomalous Features (instead of pincodes)
    feature_chart = _safe_feature_ranking(df, charts_output_dir, run_id)
    if feature_chart: chart_paths.append(feature_chart)
    
    # 3. Numeric Distribution Comparison
    dist_chart = _safe_distribution_chart(df, charts_output_dir, run_id)
    if dist_chart: chart_paths.append(dist_chart)
    
    # 4. System Health (ALWAYS works)
    health_chart = _safe_health_chart(normal_count, total_anomalies, charts_output_dir, run_id)
    if health_chart: chart_paths.append(health_chart)


def _safe_time_chart(df, charts_output_dir, run_id):
    try:
        # Find ANY datetime column
        date_col = next((c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])), None)
        if not date_col or 'is_anomaly' not in df.columns: return None
        
        df['date_plot'] = pd.to_datetime(df[date_col], errors='coerce')
        df_plot = df.dropna(subset=['date_plot'])
        if df_plot.empty: return None
        
        daily = df_plot.groupby(df_plot['date_plot'].dt.date)['is_anomaly'].sum()
        
        plt.figure(figsize=(12, 6))
        daily.plot(kind='line', marker='o', linewidth=3, color='orange')
        plt.title('Anomaly Trend Over Time')
        plt.ylabel('Daily Anomalies')
        plt.xticks(rotation=45)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        path = os.path.join(charts_output_dir, f"{run_id}_anomaly_time.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path
    except:
        plt.close()
        return None


def _safe_feature_ranking(df, charts_output_dir, run_id):
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols or 'is_anomaly' not in df.columns: return None
        
        # Top 5 features by anomaly correlation
        correlations = {}
        for col in numeric_cols[:10]:  # Limit to avoid memory issues
            if col != 'is_anomaly':
                corr = df[col].corr(df['is_anomaly'])
                correlations[col] = abs(corr) if not pd.isna(corr) else 0
        
        top_features = sorted(correlations.items(), key=lambda x: x[1], reverse=True)[:10]
        if not top_features: return None
        
        plt.figure(figsize=(10, 8))
        features, scores = zip(*top_features)
        plt.barh(range(len(features)), scores, color='coral')
        plt.yticks(range(len(features)), features)
        plt.xlabel('Anomaly Correlation')
        plt.title('Top Features by Anomaly Association')
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        
        path = os.path.join(charts_output_dir, f"{run_id}_feature_ranking.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path
    except:
        plt.close()
        return None


def _safe_distribution_chart(df, charts_output_dir, run_id):
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(numeric_cols) < 2: return None
        
        plt.figure(figsize=(12, 6))
        sample_cols = numeric_cols[:3]  # First 3 numeric columns
        
        for i, col in enumerate(sample_cols):
            plt.subplot(1, 3, i+1)
            normal = df[df['is_anomaly'] == 0][col].dropna()
            anomalous = df[df['is_anomaly'] == 1][col].dropna()
            
            if len(normal) > 0:
                plt.hist(normal, alpha=0.6, label='Normal', bins=30, color='blue')
            if len(anomalous) > 0:
                plt.hist(anomalous, alpha=0.6, label='Anomalous', bins=30, color='red')
            plt.title(col)
            plt.legend()
        
        plt.suptitle('Normal vs Anomalous Distributions')
        plt.tight_layout()
        path = os.path.join(charts_output_dir, f"{run_id}_distributions.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path
    except:
        plt.close()
        return None


def _safe_health_chart(normal_count, total_anomalies, charts_output_dir, run_id):
    try:
        plt.figure(figsize=(8, 8))
        sizes = [normal_count, total_anomalies]
        colors = ['#4CAF50', '#F44336']
        
        plt.pie(sizes, colors=colors, autopct='%1.1f%%', startangle=90, 
                explode=(0, 0.1), textprops={'fontsize': 12})
        centre_circle = plt.Circle((0,0), 0.6, fc='white')
        plt.gca().add_artist(centre_circle)
        plt.title('System Health Overview', fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        
        path = os.path.join(charts_output_dir, f"{run_id}_health.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        return path
    except:
        plt.close()
        return None
