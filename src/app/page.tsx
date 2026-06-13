import HeroSection from "@/components/sections/HeroSection";
import StatsSection from "@/components/sections/StatsSection";
import HowItWorksSection from "@/components/sections/HowItWorksSection";
import BuyFUDSXSection from "@/components/sections/BuyFUDSXSection";
import AffiliateTeaserSection from "@/components/sections/AffiliateTeaserSection";
import RecentWinnersSection from "@/components/sections/RecentWinnersSection";

export default function Home() {
  return (
    <>
      <HeroSection />
      <StatsSection />
      <HowItWorksSection />
      <BuyFUDSXSection />
      <AffiliateTeaserSection />
      <RecentWinnersSection />
    </>
  );
}
