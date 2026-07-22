import {
  attentionItems,
  diningLocations,
  quickActions,
  recentActivity,
  todaySummary,
  upcomingMenus,
} from "../data/dashboard";
import { ActivityItem } from "../components/dashboard/ActivityItem";
import { AttentionItem } from "../components/dashboard/AttentionItem";
import { DiningLocationCard } from "../components/dashboard/DiningLocationCard";
import { MealStatusCard } from "../components/dashboard/MealStatusCard";
import { QuickAction } from "../components/dashboard/QuickAction";
import { UpcomingMenuItem } from "../components/dashboard/UpcomingMenuItem";
import { DashboardPanel } from "../components/ui/DashboardPanel";
import { Icon } from "../components/ui/Icon";

export function DashboardPage() {
  return (
    <div className="p-container-padding space-y-gutter max-w-7xl mx-auto">
      {/* Section 1: Today's menu status */}
      <DashboardPanel>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="font-h2 text-h2 mb-1">{todaySummary.heading}</h2>
            <p className="text-body-sm text-secondary">
              {todaySummary.summary}
            </p>
          </div>
          <button
            type="button"
            className="bg-primary text-on-primary px-4 py-2 rounded font-bold hover:opacity-90 active:scale-95 transition-all motion-reduce:transition-none motion-reduce:active:scale-100 text-body-md flex items-center justify-center gap-2 shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            <Icon name="edit" className="text-[20px]" />
            Edit Today&apos;s Menus
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-component-gap-md">
          {todaySummary.meals.map((meal) => (
            <MealStatusCard key={meal.id} meal={meal} />
          ))}
        </div>
      </DashboardPanel>

      {/* Section 2: Needs Attention + Dining Locations */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter">
        <DashboardPanel
          title="Needs Attention"
          headerBordered
          className="lg:col-span-5"
          headerAccessory={
            <span className="bg-error-container text-on-error-container text-[11px] px-2 py-0.5 rounded font-bold">
              {attentionItems.length} ISSUES
            </span>
          }
          bodyClassName="divide-y divide-outline-variant"
        >
          {attentionItems.map((item) => (
            <AttentionItem key={item.id} item={item} />
          ))}
        </DashboardPanel>

        <section
          className="lg:col-span-7 space-y-gutter"
          aria-labelledby="dining-locations-heading"
        >
          <div className="flex justify-between items-center">
            <h3 id="dining-locations-heading" className="font-h3 text-h3">
              Dining Locations
            </h3>
            <button
              type="button"
              className="text-primary font-bold text-body-sm flex items-center gap-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              View All
              <Icon name="chevron_right" className="text-[16px]" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-component-gap-md">
            {diningLocations.map((location) => (
              <DiningLocationCard key={location.id} location={location} />
            ))}
          </div>
        </section>
      </div>

      {/* Section 3: Upcoming Menus + Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
        <DashboardPanel
          title="Upcoming Menus"
          bodyClassName="divide-y divide-outline-variant"
        >
          {upcomingMenus.map((menu) => (
            <UpcomingMenuItem key={menu.id} menu={menu} />
          ))}
        </DashboardPanel>

        <DashboardPanel title="Recent Activity" bodyClassName="space-y-4">
          {recentActivity.map((entry) => (
            <ActivityItem key={entry.id} entry={entry} />
          ))}
        </DashboardPanel>
      </div>

      {/* Section 4: Quick Actions */}
      <DashboardPanel title="Quick Actions">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-component-gap-md">
          {quickActions.map((action) => (
            <QuickAction key={action.id} action={action} />
          ))}
        </div>
      </DashboardPanel>
    </div>
  );
}
