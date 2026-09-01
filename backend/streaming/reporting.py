import pandas as pd
import matplotlib.pyplot as plt


class ReportGenerator:
    def __init__(self, snapshot):
        self.snapshot = snapshot


    def generate(self, output_path="report.png"):
        if not self.snapshot.window_history:
            return None

        df = self._prepare_dataframe()
        fig, axes = plt.subplots(3, 2, figsize=(14, 14))

        self._plot_volume_savings(df, axes[0, 0])
        self._plot_failure_rate(df, axes[0, 1])
        self._plot_settlement_composition(df, axes[1, 0])
        self._plot_cumulative_liquidity_usage(df, axes[1, 1])
        self._plot_net_positions(axes[2, 0])
        self._plot_final_balances(axes[2, 1])

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return df


    def _prepare_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self.snapshot.window_history)
        df['last_window_end'] = pd.to_datetime(df['last_window_end'])
        df.set_index('last_window_end', inplace=True)

        # Convert Decimal columns to float for plotting
        numeric_cols = [
            'total_settled', 'total_failed', 'liquidity_used', 'liquidity_saved', 'gross_volume', 'failure_rate'
        ]
        for col in numeric_cols:
            df[col] = df[col].astype(float)

        return df


    def _plot_volume_savings(self, df, axes):
        df[['gross_volume', 'total_settled', 'liquidity_saved']].plot(
            ax=axes, title="Gross vs Settled Volume & Liquidity Saved"
        )


    def _plot_failure_rate(self, df, axes):
        df[['failure_rate']].plot(ax=axes, title="Settlement Failure Rate", color='red')


    def _plot_settlement_composition(self, df, axes):
        comp_df = df[['total_settled', 'total_failed']].copy()
        comp_df.plot.bar(ax=axes, stacked=True, title="Settled vs Failed per Window")


    def _plot_cumulative_liquidity_usage(self, df, axes):
        df['liquidity_used'].plot(ax=axes, title="Cumulative Liquidity Used", color='green')


    def _plot_net_positions(self, axes):
        if not self.snapshot.net_positions:
            return
        
        net_df = pd.DataFrame(
            list(self.snapshot.net_positions.items()), columns=['Participant', 'Net Position']
        )
        colors = ['green' if v >= 0 else 'red' for v in net_df['Net Position']]
        axes.bar(net_df['Participant'], net_df['Net Position'], color=colors)
        axes.set_title("Final Net Positions (Green = Creditor, Red = Debtor)")
        axes.axhline(y=0, color='black', linewidth=0.8)


    def _plot_final_balances(self, axes):
        if not self.snapshot.balances:
            return
        
        bal_df = pd.DataFrame(
            list(self.snapshot.balances.items()), columns=['Participant', 'Balance']
        )
        axes.bar(bal_df['Participant'], bal_df['Balance'])
        axes.set_title("Final Balances")