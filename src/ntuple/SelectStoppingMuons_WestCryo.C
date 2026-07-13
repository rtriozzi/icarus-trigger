#include "TROOT.h"
#include "TTree.h"
#include "TTreeReader.h"
#include "TTreeReaderValue.h"

void SelectStoppingMuons_WestCryo(std::string iFile_, std::string oFile_, std::string oFile2_, float lifetime_ = 8.00) {
  
  // open file and read tree
  TFile *file = TFile::Open(iFile_.c_str(), "READ");
  TTreeReader treeW("t0TreeStoreW/TimedTrackStorage", file);

  // open output file in append
  std::ofstream oFile(oFile_.c_str(), std::ios_base::app);

  // optional: open output file in append
  // std::string oFile2_ = "/exp/icarus/app/users/rtriozzi/stopping_muons/calo_range.out";
  std::ofstream oFile2(oFile2_.c_str(), std::ios_base::app);

  // generic information
  TTreeReaderValue<unsigned int> run_W(treeW, "run");
  TTreeReaderValue<unsigned int> event_W(treeW, "event");

  // triggers
  TTreeReaderValue<bool> M1s_W(treeW, "M1s.fired");
  TTreeReaderValue<bool> S4s_W(treeW, "S4s.fired");
  TTreeReaderValue<bool> S5s_W(treeW, "S5s.fired");
  TTreeReaderValue<bool> S7s_W(treeW, "S7s.fired");
  TTreeReaderValue<bool> S8s_W(treeW, "S8s.fired");
  TTreeReaderValue<bool> S9s_W(treeW, "S9s.fired");
  TTreeReaderValue<bool> S10s_W(treeW, "S10s.fired");

  // time from TPC
  TTreeReaderValue<double> t0_TPC_W(treeW, "t0_TPC");

  // information from CRT
  TTreeReaderValue<double> t1_W(treeW, "entry.time");
  TTreeReaderValue<float> DCA_W(treeW, "entry.DCA");
  TTreeReaderValue<int> match_region_W(treeW, "entry.region");

  // track information
  TTreeReaderValue<float> energy_W(treeW, "energy");
  TTreeReaderValue<float> energy_int_W(treeW, "energy_int");
  TTreeReaderValue<float> energy_range_W(treeW, "energy_range");
  TTreeReaderValue<float> length_W(treeW, "length");
  TTreeReaderValue<float> dir_y_W(treeW, "dir_y");
  TTreeReaderValue<float> atcathode_x_W(treeW, "atcathode_x");

  // reconstructed coordinates
  TTreeReaderValue<float> start_x_W(treeW, "start_x");
  TTreeReaderValue<float> start_y_W(treeW, "start_y");
  TTreeReaderValue<float> start_z_W(treeW, "start_z");
  TTreeReaderValue<float> middle_x_W(treeW, "middle_x");
  TTreeReaderValue<float> middle_y_W(treeW, "middle_y");
  TTreeReaderValue<float> middle_z_W(treeW, "middle_z");
  TTreeReaderValue<float> end_x_W(treeW, "end_x");
  TTreeReaderValue<float> end_y_W(treeW, "end_y");
  TTreeReaderValue<float> end_z_W(treeW, "end_z");

  // flash information
  TTreeReaderValue<float> closest_flash_t_W(treeW, "closestFlash.flash_time");
  TTreeReaderValue<float> closest_flash_y_W(treeW, "closestFlash.flash_y");
  TTreeReaderValue<float> closest_flash_z_W(treeW, "closestFlash.flash_z");
  TTreeReaderValue<float> nearest_flash_t_W(treeW, "nearestFlash.flash_time");
  TTreeReaderValue<float> nearest_flash_y_W(treeW, "nearestFlash.flash_y");
  TTreeReaderValue<float> nearest_flash_z_W(treeW, "nearestFlash.flash_z");

  // calorimetric information
  TTreeReaderArray<float> rr_W(treeW, "selHits.rr");
  TTreeReaderArray<float> pitch_W(treeW, "selHits.pitch");
  TTreeReaderArray<float> dedx_W(treeW, "selHits.dEdx");
  TTreeReaderArray<float> px_W(treeW, "selHits.px");
  TTreeReaderArray<float> py_W(treeW, "selHits.py");
  TTreeReaderArray<float> pz_W(treeW, "selHits.pz");

  // parameters
  const int offset = 10;
  const float yh = 134.96, yl = -181.86, xh = 358.73, xl = 61.7, zh = 894.951, zl = -894.951;
  const float cathode_x = 210.29;
  float start_x, start_y, start_z, end_x, end_y, end_z;
  bool mask_top, mask_sides_x_1, mask_sides_x_2, mask_sides_z_1, mask_sides_z_2, mask_start, mask_fv, mask_cathode, mask_z0;
  unsigned int i_min, i_max;
  vector<float> dqdx_last_hits_cal;
  float median_dqdx_last_hits_cal = 0., energy_my_cal_W = 0., energy_last_20_cm_W = 0.;
  const float lifetime = lifetime_ * 1.e6 / 400.;

  std::cout << "Starting analysis..." << std::endl;

  // start loop on TTree
  while(treeW.Next())
  {

    /*
     *  Pre-selection. Time from CRT within PMT readout; DCA < 30 cm;
     *  vertical direction must be negative for downward-going muon.
     */

    // apply pre-selection
    if (*t1_W > -49 && *t1_W < 117 && *DCA_W < 30 && *dir_y_W < 0) {

      // default values
      start_x = -99999;
      start_y = -99999;
      start_z = -99999;
      end_x = -99999;
      end_y = -99999;
      end_z = -99999;

      // search for starting point
      if (px_W.GetSize() > 2) {

        for (int i = px_W.GetSize()-1; i >= 0; i--) {

          // if space point is reconstructed
          if (px_W[i] > -20000) {

            // store first valid hit as starting point
            start_y = py_W[i];
            start_z = pz_W[i];

            // shift the x only if not cathode-crossing
            if (*atcathode_x_W < -20000) {
              start_x = px_W[i] - 0.156 * (*t1_W);
            }
            else {
              start_x = px_W[i];
            }

            // found starting point
            break;
          }
        }

        // search for stopping point
        for (unsigned int i = 0; i < px_W.GetSize(); i++) {

          // if space point is reconstructed
          if (px_W[i] > -20000) {

            // store last valid hit as stopping point
            end_y = py_W[i];
            end_z = pz_W[i];

            // shift the x only if not cathode-crossing
            if (*atcathode_x_W < -20000) {
              end_x = px_W[i] - 0.156 * (*t1_W);
            }
            else {
              end_x = px_W[i];
            }

            // found stopping point
            break;
          }
        }
      } // end of condition on non-emptiness 

      // start coordinate near the TPC walls 
      mask_top = (start_y >= yh-offset) & (start_y <= yh) & (start_z >= zl) & (start_z <= zh) & (start_x >= xl) & (start_x <= xh);
      mask_sides_x_1 =  (start_y >= yl) & (start_y <= yh) & (start_z >= zl) & (start_z <= zl+offset) & (start_x >= xl) & (start_x <= xh);
      mask_sides_x_2 =  (start_y >= yl) & (start_y <= yh) & (start_z >= zh-offset) & (start_z <= zh) & (start_x >= xl) & (start_x <= xh);
      mask_sides_z_1 = (start_y >= yl) & (start_y <= yh) & (start_z >= zl) & (start_z <= zh) & (start_x >= xl) & (start_x <= xl+offset);
      mask_sides_z_2 = (start_y >= yl) & (start_y <= yh) & (start_z >= zl) & (start_z <= zh) & (start_x >= xh-offset) & (start_x <= xh);
      mask_start = mask_top || mask_sides_x_1 || mask_sides_x_2 || mask_sides_z_1 || mask_sides_z_2;

      // fiducialize for the stop coordinate 
      mask_fv = (end_x >= xl+offset) & (end_x <= xh-offset) & (end_y >= yl+offset) & (end_y <= yh-offset) & (end_z >= zl+offset) & (end_z <= zh-offset);
      mask_cathode = (end_x <= cathode_x-5) || (end_x >= cathode_x+5);
      mask_z0 = (end_z <= -5) || (end_z >= 5);

      /*
       *  Apply start and end conditions.
       */

      if (mask_start && mask_fv && mask_cathode && mask_z0) {

        // default values
        i_min = 1e5;
        i_max = 0;

        // get indeces of 0 cm < residual range < 5 cm, i.e., last 5 cm of track
        for (unsigned int i = 0; i < rr_W.GetSize(); i++) {
            if (rr_W[i] >= 0) 
              if (i <= i_min)
                i_min = i;
            if (rr_W[i] <= 5)
              if (i >= i_max)
                i_max = i;
        }

        // get calorimetry in the last hits, calibrated
        dqdx_last_hits_cal.clear();

        // skip the hits nearest to the zero residual range!
        for (unsigned int i = i_min + 1; i <= i_max; i++) {

          dqdx_last_hits_cal.push_back(dedx_W[i]);
        }

        // compute median of calorimetry in the last hits
        if (dqdx_last_hits_cal.size() > 0) {
          if (dqdx_last_hits_cal.size() % 2 == 0) {
            median_dqdx_last_hits_cal = (dqdx_last_hits_cal[dqdx_last_hits_cal.size() / 2 - 1] + dqdx_last_hits_cal[dqdx_last_hits_cal.size() / 2]) / 2;
          }
          else {
            median_dqdx_last_hits_cal = dqdx_last_hits_cal[dqdx_last_hits_cal.size() / 2];
          }
        }

        /*
         * Median selection (as of now, in MeV).
         */

        if ((dqdx_last_hits_cal.size() > 5) & (median_dqdx_last_hits_cal > 4)) {

          /*
           *  Scan the last 20 cm to get some values.
           */
          // default values
          i_min = 1e6;
          i_max = 0;

          // get indeces of the whole track
          for (unsigned int i = 0; i < rr_W.GetSize(); i++) {
              if (rr_W[i] >= 0.) 
                if (i <= i_min)
                  i_min = i;
              if (rr_W[i] <= 20)
                if (i >= i_max)
                  i_max = i;
          } 

          // default value
          energy_last_20_cm_W = 0.;

          for (unsigned int i = i_min; i <= i_max; i++) {

              // get calibrated energy in the last 20 cm
              energy_last_20_cm_W += pitch_W[i] * dedx_W[i];

          }
          
          for (unsigned int i = i_min; i <= i_max; i++) {

              // store dQ/dx vs RR information
              oFile2 << *length_W << "\t" << *energy_W << "\t" << *end_x_W << "\t" << *end_y_W << "\t" << *end_z_W << "\t" << median_dqdx_last_hits_cal << "\t" << energy_last_20_cm_W << "\t" <<  rr_W[i] << "\t" << dedx_W[i] << std::endl;
          }
  
          // debug
          std::cout << i_min << "\t" << i_max << "\t" << *length_W << "\t" << energy_last_20_cm_W << "\t" << energy_my_cal_W << "\t" << *energy_W << std::endl;

          // store selected event
          oFile << *run_W << "\t" << *event_W << "\t" << *length_W << "\t" << *energy_W << "\t" << *energy_range_W << "\t" << *t0_TPC_W << "\t" << *t1_W << "\t" << *dir_y_W << "\t" 
          << *S4s_W << "\t" << *S5s_W << "\t" << *S7s_W << "\t" << *S9s_W << "\t" << *S10s_W << "\t" 
          << start_x << "\t" << end_x << "\t" << start_y << "\t" << end_y << "\t" << start_z << "\t" << end_z << "\t" 
          << *start_x_W << "\t" << *middle_x_W << "\t" << *end_x_W << "\t" << *start_y_W << "\t" << *middle_y_W << "\t" << *end_y_W << "\t" << *start_z_W << "\t" << *middle_z_W << "\t" << *end_z_W << "\t" 
          << median_dqdx_last_hits_cal << "\t" << dqdx_last_hits_cal.size() << "\t" << energy_my_cal_W << "\t" << energy_last_20_cm_W << "\t"
          << *closest_flash_t_W << "\t" << *closest_flash_y_W << "\t" << *closest_flash_z_W << "\t" 
          << *nearest_flash_t_W << "\t" << *nearest_flash_y_W << "\t" << *nearest_flash_z_W << "\t" << std::endl;

        } // end of median selection
      } // end of start and end selections
    } // end of pre-selection
  }
  
  // optional
  oFile2.close();

  // close files
  oFile.close();
  file->cd();
  file->Close();

  return;

}