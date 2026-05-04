import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from algorithms.utils import format_time

def create_algorithm_comparison_chart(algorithm_results):
    """
    Create a comparison chart for different algorithms.
    
    Args:
        algorithm_results: dict with algorithm names as keys and
                          (distance, time) tuples as values
                          Example: {
                              'Dijkstra': (5000, 600),
                              'A*': (5000, 610),
                              'Dynamic Routing': (5200, 780),
                              'VRP': (5300, 700)
                          }
    
    Returns:
        Plotly figure object
    """
    if not algorithm_results:
        return None
    
    algorithms = list(algorithm_results.keys())
    times = [algorithm_results[algo][1] for algo in algorithms]
    distances = [algorithm_results[algo][0] for algo in algorithms]
    
    # Calculate speeds (distance / time in km/h)
    speeds = [
        (dist / time * 3.6) if time > 0 else 0 
        for dist, time in zip(distances, times)
    ]
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add time bar chart
    fig.add_trace(go.Bar(
        x=algorithms,
        y=times,
        name='Travel Time (seconds)',
        marker_color='indianred',
        yaxis='y1'
    ))
    
    # Add speed line chart
    fig.add_trace(go.Scatter(
        x=algorithms,
        y=speeds,
        name='Speed (km/h)',
        mode='lines+markers',
        line=dict(color='green', width=3),
        marker=dict(size=10),
        yaxis='y2'
    ))
    
    # Update layout with secondary y-axis
    fig.update_layout(
        title='Algorithm Comparison: Time and Speed Analysis',
        xaxis=dict(title='Algorithm'),
        yaxis=dict(
            title=dict(text='Travel Time (seconds)', font=dict(color='indianred')),
            tickfont=dict(color='indianred')
        ),
        yaxis2=dict(
            title=dict(text='Speed (km/h)', font=dict(color='green')),
            tickfont=dict(color='green'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )
    
    return fig

def create_distance_time_scatter(algorithm_results):
    """
    Create a scatter plot showing distance vs time trade-off.
    """
    if not algorithm_results:
        return None
    
    algorithms = list(algorithm_results.keys())
    times = [algorithm_results[algo][1] for algo in algorithms]
    distances = [algorithm_results[algo][0] / 1000 for algo in algorithms]  # Convert to km
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=distances,
        y=times,
        mode='markers+text',
        marker=dict(size=12, color=times, colorscale='Viridis', showscale=True),
        text=algorithms,
        textposition='top center',
        name='Algorithms'
    ))
    
    fig.update_layout(
        title='Algorithm Performance: Distance vs Time Trade-off',
        xaxis=dict(title='Distance (km)'),
        yaxis=dict(title='Time (seconds)'),
        height=500,
        template='plotly_white'
    )
    
    return fig

def create_performance_metrics_table(algorithm_results):
    """
    Create a detailed metrics table for algorithm comparison.
    """
    if not algorithm_results:
        return None
    
    data = {
        'Algorithm': [],
        'Distance (m)': [],
        'Time': [],
        'Speed (km/h)': [],
        'Efficiency': []
    }
    
    for algo, (dist, time) in algorithm_results.items():
        data['Algorithm'].append(algo)
        data['Distance (m)'].append(f"{dist:.0f}")
        data['Time'].append(format_time(time))
        
        speed = (dist / time * 3.6) if time > 0 else 0
        data['Speed (km/h)'].append(f"{speed:.2f}")
        
        # Efficiency: lower time is better (100 = best)
        min_time = min([v[1] for v in algorithm_results.values()])
        efficiency = (min_time / time * 100) if time > 0 else 0
        data['Efficiency'].append(f"{efficiency:.1f}%")
    
    return data

def display_algorithm_comparison(algorithm_results):
    """
    Display comprehensive algorithm comparison in Streamlit.
    """
    if not algorithm_results:
        st.warning("No algorithm results to compare. Please compute routes first.")
        return
    
    # Debug section - Show raw computed values
    with st.expander("🔍 Raw Computed Values (Debug)", expanded=False):
        st.write("**Raw algorithm results:**")
        debug_data = {
            'Algorithm': [],
            'Distance (m)': [],
            'Time (s)': [],
            'Speed (km/h)': []
        }
        for algo, (dist, time) in algorithm_results.items():
            debug_data['Algorithm'].append(algo)
            debug_data['Distance (m)'].append(f"{dist:.2f}")
            debug_data['Time (s)'].append(f"{time:.2f}")
            speed = (dist / time * 3.6) if time > 0 else 0
            debug_data['Speed (km/h)'].append(f"{speed:.4f}")
        st.dataframe(debug_data)
    
    st.header("Algorithm Comparison Analysis")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["📊 Time & Speed", "📈 Distance vs Time", "📋 Metrics Table"])
    
    with tab1:
        fig = create_algorithm_comparison_chart(algorithm_results)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = create_distance_time_scatter(algorithm_results)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        metrics_data = create_performance_metrics_table(algorithm_results)
        if metrics_data:
            st.dataframe(metrics_data, use_container_width=True)
            
            # Summary statistics
            st.subheader("Summary")
            times = [v[1] for v in algorithm_results.values()]
            fastest_algo = min(algorithm_results.keys(), key=lambda x: algorithm_results[x][1])
            slowest_algo = max(algorithm_results.keys(), key=lambda x: algorithm_results[x][1])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fastest", fastest_algo, f"{algorithm_results[fastest_algo][1]:.0f}s")
            with col2:
                st.metric("Slowest", slowest_algo, f"{algorithm_results[slowest_algo][1]:.0f}s")
            with col3:
                time_diff = algorithm_results[slowest_algo][1] - algorithm_results[fastest_algo][1]
                st.metric("Time Difference", f"{time_diff:.0f}s", f"{(time_diff/algorithm_results[fastest_algo][1]*100):.1f}% slower")
