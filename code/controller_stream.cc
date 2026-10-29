#include "comnet/security-orchestrator.h"
#include <iostream>
#include <string>
using namespace comnet;
int main(int argc,char**argv){
 if(argc!=2) return 2;
 const std::string policy=argv[1];
 if(policy!="P4" && policy!="A1" && policy!="B2" && policy!="B5") return 2;
 // Development-only parameters from M2-R2, NOT independently calibrated.
 const RiskWeights weights{1.,0.,0.};
 const OrchestratorThresholds th{.20,.40,.75,.20,.40,.75,3};
 OrchestratorMemory memory{};
 std::cout<<"tick,state,counter,risk,pressure,filter,traffic,edge,cadence"<<std::endl;
 unsigned tick;double probability,auth,edge,queue,latency,processing;
 while(std::cin>>tick>>probability>>auth>>edge>>queue>>latency>>processing){
  OrchestratorObservation o{probability,auth,edge,queue,latency,processing};
  if(policy=="A1"){o.queuePressure=0;o.latencyPressure=0;o.securityProcessingPressure=0;}
  SecurityState state=SecurityState::NORMAL;double risk=0,pressure=0;unsigned counter=0;
  if(policy!="B2"){
   auto d=SecurityOrchestrator::Advance(memory,o,weights,th);
   memory={d.state,d.belowRecoveryThresholdWindows};
   state=d.state;risk=d.riskScore;pressure=d.pressureScore;counter=memory.belowRecoveryThresholdWindows;
  }else{
   SecurityOrchestrator::ValidateObservation(o);
   risk=SecurityOrchestrator::RiskScore(o,weights);
   pressure=SecurityOrchestrator::PressureScore(o);
   state=SecurityState::ELEVATED; // Explicit STATIC-ELEVATED B2 candidate; NOT validated static-full security.
  }
  auto a=SecurityOrchestrator::ActionProfile(state);
  std::cout<<tick<<','<<SecurityOrchestrator::ToString(state)<<','<<counter<<','<<risk<<','<<pressure<<','<<SecurityOrchestrator::ToString(a.filtering)<<','<<SecurityOrchestrator::ToString(a.trafficTreatment)<<','<<SecurityOrchestrator::ToString(a.edgeResponse)<<','<<a.detectorCadenceSeconds<<std::endl;
 }
}
